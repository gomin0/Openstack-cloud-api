import asyncio
import logging
from logging import Logger

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.response import ServerDetailsResponse, ServerDetailResponse, ServerResponse, \
    DeleteServerResponse
from common.domain.enum import SortOrder
from common.domain.floating_ip.entity import FloatingIp
from common.domain.network_interface.entity import NetworkInterface
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.domain.volume.entity import Volume
from common.exception.server_exception import ServerNotFoundException, ServerNameDuplicateException, \
    ServerDeletionFailedException
from common.exception.volume_exception import VolumeNotFoundException
from common.infrastructure.database import transactional
from common.infrastructure.network_interface.repository import NetworkInterfaceRepository
from common.infrastructure.network_interface_security_group.repository import NetworkInterfaceSecurityGroupRepository
from common.infrastructure.neutron.client import NeutronClient
from common.infrastructure.nova.client import NovaClient
from common.infrastructure.server.repository import ServerRepository
from common.infrastructure.volume.repository import VolumeRepository
from common.util.envs import get_envs, Envs

envs: Envs = get_envs()
logger: Logger = logging.getLogger(__name__)


class ServerService:
    MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION: int = envs.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION
    CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION: int = envs.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION

    def __init__(
        self,
        server_repository: ServerRepository = Depends(),
        volume_repository: VolumeRepository = Depends(),
        network_interface_repository: NetworkInterfaceRepository = Depends(),
        network_interface_security_group_repository: NetworkInterfaceSecurityGroupRepository = Depends(),
        nova_client: NovaClient = Depends(),
        neutron_client: NeutronClient = Depends()
    ):
        self.server_repository = server_repository
        self.volume_repository = volume_repository
        self.network_interface_repository = network_interface_repository
        self.network_interface_security_group_repository = network_interface_security_group_repository
        self.nova_client = nova_client
        self.neutron_client = neutron_client

    @transactional()
    async def find_servers_details(
        self,
        session: AsyncSession,
        id_: int | None,
        ids_contain: list[int] | None,
        ids_exclude: list[int] | None,
        name_eq: str | None,
        name_like: str | None,
        sort_by: ServerSortOption,
        order: SortOrder,
        project_id: int,
    ) -> ServerDetailsResponse:
        servers: list[Server] = await self.server_repository.find_all_by_project_id(
            session=session,
            id_=id_,
            ids_contain=ids_contain,
            ids_exclude=ids_exclude,
            name_eq=name_eq,
            name_like=name_like,
            sort_by=sort_by,
            order=order,
            project_id=project_id,
            with_relations=True,
        )
        return ServerDetailsResponse(servers=[await ServerDetailResponse.from_entity(server) for server in servers])

    @transactional()
    async def get_server_detail(
        self,
        session: AsyncSession,
        server_id: int,
        project_id: int,
    ) -> ServerDetailResponse:
        server: Server | None = await self._get_server_by_id(session=session, server_id=server_id, with_relations=True)
        server.validate_access_permission(project_id=project_id)

        return await ServerDetailResponse.from_entity(server)

    @transactional()
    async def update_server_info(
        self,
        session: AsyncSession,
        current_project_id: int,
        server_id: int,
        name: str,
        description: str,
    ) -> ServerResponse:
        server: Server | None = await self.server_repository.find_by_id(session=session, server_id=server_id)
        if server is None:
            raise ServerNotFoundException()
        server.validate_update_permission(project_id=current_project_id)

        if name != server.name:
            if await self.server_repository.exists_by_project_and_name(
                session=session,
                project_id=current_project_id,
                name=name
            ):
                raise ServerNameDuplicateException()

        server.update_info(name=name, description=description)
        return ServerResponse.from_entity(server)

    @transactional()
    async def get_server(
        self,
        session: AsyncSession,
        server_id: int,
        project_id: int,
    ) -> ServerResponse:
        server: Server = await self.server_repository.find_by_id(
            session=session,
            server_id=server_id,
        )
        if server is None:
            raise ServerNotFoundException()
        server.validate_access_permission(project_id=project_id)

        return ServerResponse.from_entity(server)

    async def get_vnc_console(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
    ) -> str:
        vnc_url: str = await self.nova_client.get_vnc_console(
            client=client,
            keystone_token=keystone_token,
            server_openstack_id=server_openstack_id
        )

        return vnc_url

    @transactional()
    async def delete_server(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        server_id: int,
        project_id: int
    ) -> DeleteServerResponse:
        server: Server = await self._get_server_by_id(session=session, server_id=server_id)
        server.validate_delete_permission(project_id=project_id)

        network_interfaces: list[NetworkInterface] = await server.network_interfaces
        network_interface_ids: list[int] = [network_interface.id for network_interface in network_interfaces]

        volumes: list[Volume] = await server.volumes
        root_volume_id: int | None = next((volume.id for volume in volumes if volume.is_root_volume), None)

        await self.nova_client.delete_server(
            client=client,
            keystone_token=keystone_token,
            server_openstack_id=server.openstack_id,
        )

        return DeleteServerResponse(
            server_id=server.id,
            volume_id=root_volume_id,
            network_interface_ids=network_interface_ids,
        )

    async def check_server_and_remove_resources(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        network_interface_ids: list[int],
        server_id: int,
    ) -> None:
        await self.remove_server_resources(
            session=session,
            client=client,
            keystone_token=keystone_token,
            server_id=server_id,
            network_interface_ids=network_interface_ids,
        )
        await self.check_server_deletion_and_remove(
            session=session,
            client=client,
            keystone_token=keystone_token,
            server_id=server_id,
        )

    @transactional()
    async def check_server_deletion_and_remove(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        server_id: int,
    ) -> None:
        server: Server = await self._get_server_by_id(session=session, server_id=server_id)

        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION):
            is_server_deleted: bool = not await self.nova_client.exists_server(
                client=client,
                keystone_token=keystone_token,
                server_openstack_id=server.openstack_id,
            )
            if is_server_deleted:
                server.delete()
                break
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION)
        else:
            logger.error(
                f"서버({server.openstack_id})를 삭제 시도했으나, "
                f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION}초 동안 "
                f"정상적으로 삭제되지 않았습니다."
            )
            raise ServerDeletionFailedException()

    @transactional()
    async def remove_server_resources(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        server_id: int,
        network_interface_ids: list[int],
    ) -> None:
        server: Server = await self._get_server_by_id(session=session, server_id=server_id)
        volumes: list[Volume] = await server.volumes
        for volume in volumes:
            volume.detach_from_server()

        network_interfaces: list[NetworkInterface] = await self.network_interface_repository.find_all_by_ids(
            session=session, network_interface_ids=network_interface_ids
        )
        for network_interface in network_interfaces:
            await network_interface.detach_all_security_groups()
            network_interface.delete()
            floating_ip: FloatingIp = await network_interface.floating_ip
            if floating_ip:
                floating_ip.detach_from_network_interface()

        tasks = [
            self.neutron_client.delete_network_interface(
                client=client,
                keystone_token=keystone_token,
                network_interface_openstack_id=network_interface.openstack_id
            )
            for network_interface in network_interfaces
        ]
        await asyncio.gather(*tasks)

    async def _get_server_by_id(
        self,
        session: AsyncSession,
        server_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> Server:
        if (
            server := await self.server_repository.find_by_id(
                session=session,
                server_id=server_id,
                with_deleted=with_deleted,
                with_relations=with_relations,
            )
        ) is None:
            raise ServerNotFoundException()
        return server

    async def _get_volume_by_id(
        self,
        session: AsyncSession,
        volume_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> Volume:
        if (
            server := await self.volume_repository.find_by_id(
                session=session,
                volume_id=volume_id,
                with_deleted=with_deleted,
                with_relations=with_relations,
            )
        ) is None:
            raise VolumeNotFoundException()
        return server
