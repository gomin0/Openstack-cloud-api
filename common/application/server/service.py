import asyncio
import logging
from logging import Logger

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.response import ServerDetailsResponse, ServerDetailResponse, ServerResponse
from common.domain.enum import SortOrder
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.domain.volume.dto import OsVolumeDto
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.server_exception import ServerNotFoundException, ServerNameDuplicateException, \
    VolumeDetachFailedException
from common.exception.volume_exception import VolumeNotFoundException
from common.infrastructure.cinder.client import CinderClient
from common.infrastructure.database import transactional
from common.infrastructure.nova.client import NovaClient
from common.infrastructure.server.repository import ServerRepository
from common.infrastructure.volume.repository import VolumeRepository
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()
logger: Logger = logging.getLogger(__name__)


class ServerService:
    MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT: int = envs.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT
    CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT: int = envs.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT

    def __init__(
        self,
        server_repository: ServerRepository = Depends(),
        volume_repository: VolumeRepository = Depends(),
        nova_client: NovaClient = Depends(),
        cinder_client: CinderClient = Depends()
    ):
        self.server_repository = server_repository
        self.volume_repository = volume_repository
        self.nova_client = nova_client
        self.cinder_client = cinder_client

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

    async def detach_volume_from_server(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
        project_id: int,
        server_id: int,
        volume_id: int
    ) -> ServerDetailResponse:
        server: Server
        volume: Volume
        server, volume = await self._initiate_volume_detachment(
            session=session,
            client=client,
            keystone_token=keystone_token,
            project_id=project_id,
            server_id=server_id,
            volume_id=volume_id,
        )
        is_success: bool = await self._wait_until_volume_detach_and_finalize(
            session=session,
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=project_openstack_id,
            volume_openstack_id=volume.openstack_id
        )
        if not is_success:
            raise VolumeDetachFailedException()
        return await ServerDetailResponse.from_entity(server)

    @transactional()
    async def _initiate_volume_detachment(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        server_id: int,
        volume_id: int
    ) -> tuple[Server, Volume]:
        volume: Volume = await self._get_volume_by_id(session=session, volume_id=volume_id)
        volume.validate_owned_by(project_id=project_id)
        volume.validate_server_match(server_id=server_id)
        volume.prepare_for_detachment()

        server: Server = await self._get_server_by_id(session=session, server_id=server_id)
        await self.nova_client.detach_volume_from_server(
            client=client,
            keystone_token=keystone_token,
            server_openstack_id=server.openstack_id,
            volume_openstack_id=volume.openstack_id,
        )

        return server, volume

    @transactional()
    async def _wait_until_volume_detach_and_finalize(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        volume_openstack_id: str,
        project_openstack_id: str
    ) -> bool:
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT)

            os_volume: OsVolumeDto = await self.cinder_client.get_volume(
                client=client,
                keystone_token=keystone_token,
                project_openstack_id=project_openstack_id,
                volume_openstack_id=volume_openstack_id,
            )

            if os_volume.status in [VolumeStatus.IN_USE, VolumeStatus.DETACHING]:
                continue
            if os_volume.status == VolumeStatus.AVAILABLE:
                volume: Volume = \
                    await self._get_volume_by_openstack_id(session=session, openstack_id=volume_openstack_id)
                volume.detach_from_server()
                volume.update_to_available()
                return True
            logger.error(f"볼륨({volume_openstack_id}) 연결 해제 도중 에러가 발생했습니다. status={os_volume.status}")
            volume: Volume = await self._get_volume_by_openstack_id(session=session, openstack_id=volume_openstack_id)
            volume.update_status(status=os_volume.status)
            return False

        logger.error(
            f"볼륨({volume_openstack_id}) 연결 해제를 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT * self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT}초 동안 "
            f"정상적으로 해제되지 않았습니다."
        )
        return False

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
            volume := await self.volume_repository.find_by_id(
                session=session,
                volume_id=volume_id,
                with_deleted=with_deleted,
                with_relations=with_relations,
            )
        ) is None:
            raise VolumeNotFoundException()
        return volume

    async def _get_volume_by_openstack_id(self, session, openstack_id):
        if (volume := await self.volume_repository.find_by_openstack_id(session, openstack_id)) is None:
            raise VolumeNotFoundException()
        return volume
