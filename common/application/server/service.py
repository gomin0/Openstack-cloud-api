import asyncio
import logging
import uuid
from logging import Logger

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.dto import CreateServerCommand
from common.application.server.response import ServerDetailsResponse, ServerDetailResponse, ServerResponse
from common.domain.enum import SortOrder
from common.domain.network_interface.dto import OsNetworkInterfaceDto
from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.entity import SecurityGroup
from common.domain.server.dto import OsServerDto
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption, ServerStatus
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.server_exception import ServerNotFoundException, ServerNameDuplicateException
from common.infrastructure.database import transactional
from common.infrastructure.network_interface.repository import NetworkInterfaceRepository
from common.infrastructure.neutron.client import NeutronClient
from common.infrastructure.nova.client import NovaClient
from common.infrastructure.security_group.repository import SecurityGroupRepository
from common.infrastructure.server.repository import ServerRepository
from common.infrastructure.volume.repository import VolumeRepository
from common.util.compensating_transaction import CompensationManager
from common.util.envs import get_envs, Envs

logger: Logger = logging.getLogger(__name__)
envs: Envs = get_envs()


class ServerService:
    MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION: int = envs.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION
    CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION: int = envs.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION

    def __init__(
        self,
        server_repository: ServerRepository = Depends(),
        volume_repository: VolumeRepository = Depends(),
        network_interface_repository: NetworkInterfaceRepository = Depends(),
        security_group_repository: SecurityGroupRepository = Depends(),
        nova_client: NovaClient = Depends(),
        neutron_client: NeutronClient = Depends(),
    ):
        self.server_repository = server_repository
        self.volume_repository = volume_repository
        self.network_interface_repository = network_interface_repository
        self.security_group_repository = security_group_repository
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
        server: Server | None = await self._get_server_by_id(session=session, id_=server_id, with_relations=True)
        server.validate_access_permission(project_id=project_id)

        return await ServerDetailResponse.from_entity(server)

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
    async def create_server(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        command: CreateServerCommand,
    ) -> ServerResponse:
        """
        요청 정보를 받아 서버를 생성합니다.

        서버가 생성될 때 다음 작업들이 함꼐 진행됩니다.

        - Network Interface 생성
        - Network Interface에 Security Groups 적용
        - 루트 볼륨 생성
        - 서버에 루트 볼륨 연결
        - 서버에 Network Interface 연결

        서버 생성 작업은 비동기로 동작하기에, `ServerService.finalize_server_creation()`를 통해 후처리 작업을 진행해야 합니다.

        :return: 생성된 서버 정보
        """
        is_exists_name: bool = await self.server_repository.exists_by_project_and_name(
            session=session,
            project_id=command.current_project_id,
            name=command.name,
        )
        if is_exists_name:
            raise ServerNameDuplicateException()

        security_groups: list[SecurityGroup] = await self.security_group_repository.find_all_by_ids(
            session=session,
            ids=command.security_group_ids
        )
        for sg in security_groups:
            sg.validate_accessible_by(project_id=command.current_project_id)

        os_network_interface: OsNetworkInterfaceDto = await self.neutron_client.create_network_interface(
            client=client,
            keystone_token=command.keystone_token,
            network_openstack_id=command.network_openstack_id,
            security_group_openstack_ids=[sg.openstack_id for sg in security_groups],
        )
        compensating_tx.add_task(
            lambda: self.neutron_client.delete_network_interface(
                client=client,
                keystone_token=command.keystone_token,
                network_interface_openstack_id=os_network_interface.openstack_id
            )
        )

        server_openstack_id: str = await self.nova_client.create_server(
            client=client,
            keystone_token=command.keystone_token,
            flavor_openstack_id=command.flavor_openstack_id,
            image_openstack_id=command.root_volume.image_openstack_id,
            network_interface_openstack_id=os_network_interface.openstack_id,
            root_volume_size=command.root_volume.size
        )
        compensating_tx.add_task(
            lambda: self.nova_client.delete_server(
                client=client,
                keystone_token=command.keystone_token,
                server_openstack_id=server_openstack_id,
            )
        )

        server: Server = await self.server_repository.create(
            session=session,
            server=Server.create(
                openstack_id=server_openstack_id,
                project_id=command.current_project_id,
                flavor_openstack_id=command.flavor_openstack_id,
                name=command.name,
                description=command.description,
            )
        )
        network_interface: NetworkInterface = await self.network_interface_repository.create(
            session=session,
            network_interface=NetworkInterface.create(
                openstack_id=os_network_interface.openstack_id,
                project_id=command.current_project_id,
                server_id=server.id,
                fixed_ip_address=os_network_interface.fixed_ip_address,
            )
        )
        await network_interface.add_security_groups(security_groups=security_groups)

        return ServerResponse.from_entity(server)

    @transactional()
    async def update_server_info(
        self,
        session: AsyncSession,
        current_project_id: int,
        server_id: int,
        name: str,
        description: str,
    ) -> ServerResponse:
        server: Server | None = await self._get_server_by_id(session=session, id_=server_id)
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
    async def finalize_server_creation(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
        image_openstack_id: str,
        root_volume_size: int
    ) -> None:
        """
        `ServerService.create_server()`에서 서버 생성을 한 후, 서버 생성이 완료될 때까지 대기합니다.

        이후 서버 생성이 완료되었다면, 서버 생성 완료 후에 처리해야 할 작업들을 수행합니다.

        - 서버를 활성(ACTIVE) 상태로 변경
        - 볼륨 데이터를 DB에 생성(INSERT)
        """
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION)

            os_server: OsServerDto = await self.nova_client.get_server(
                client=client,
                keystone_token=keystone_token,
                server_openstack_id=server_openstack_id,
            )

            if os_server.status == ServerStatus.BUILD:
                continue

            if os_server.status == ServerStatus.ACTIVE:
                root_volume_openstack_id: str = os_server.volume_openstack_ids[0]

                server: Server = \
                    await self._get_server_by_openstack_id(session=session, openstack_id=server_openstack_id)
                server.active()
                await self.volume_repository.create(
                    session=session,
                    # 서버 생성 시, volume type을 받게 된다면, 하드 코딩된 값 수정 필요
                    volume=Volume.create(
                        openstack_id=root_volume_openstack_id,
                        project_id=server.project_id,
                        server_id=server.id,
                        volume_type_openstack_id="64a19e22-a30b-4982-8f82-332e89ff4bf7",
                        image_openstack_id=image_openstack_id,
                        name=f"volume_{uuid.uuid4()}",
                        description="",
                        status=VolumeStatus.AVAILABLE,
                        size=root_volume_size,
                        is_root_volume=True,
                    )
                )
                return

            logger.error(f"서버 생성에 실패했습니다. Server openstack_id={server_openstack_id} status={os_server.status}")
            break
        else:
            logger.error(
                f"서버 생성에 실패했습니다. 생성중인 서버 {server_openstack_id}가 "
                f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION}초 "
                f"동안 생성이 완료되기를 기다렸으나, 생성이 완료되지 않았습니다."
            )
        server: Server = await self._get_server_by_openstack_id(session=session, openstack_id=server_openstack_id)
        server.fail_creation()

    async def _get_server_by_id(
        self,
        session: AsyncSession,
        id_: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> Server:
        if (server := await self.server_repository.find_by_id(session, id_, with_deleted, with_relations)) is None:
            raise ServerNotFoundException()
        return server

    async def _get_server_by_openstack_id(
        self,
        session: AsyncSession,
        openstack_id: str,
        with_deleted: bool = False,
    ):
        if (server := await self.server_repository.find_by_openstack_id(session, openstack_id, with_deleted)) is None:
            raise ServerNotFoundException()
        return server
