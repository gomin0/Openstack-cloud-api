import asyncio
import logging
from logging import Logger

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.response import ServerDetailsResponse, ServerDetailResponse, ServerResponse
from common.domain.enum import SortOrder
from common.domain.server.dto import OsServerDto
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption, ServerStatus
from common.exception.server_exception import ServerNotFoundException, ServerNameDuplicateException
from common.infrastructure.database import transactional
from common.infrastructure.nova.client import NovaClient
from common.infrastructure.server.repository import ServerRepository
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()
logger: Logger = logging.getLogger(__name__)


class ServerService:
    MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE: int = envs.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE
    CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE: int = envs.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE

    def __init__(
        self,
        server_repository: ServerRepository = Depends(),
        nova_client: NovaClient = Depends()
    ):
        self.server_repository = server_repository
        self.nova_client = nova_client

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
    async def start_server(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        server_id: int,
    ) -> ServerResponse:
        server: Server = await self._get_server_by_id(session=session, server_id=server_id)
        server.validate_access_permission(project_id=project_id)
        server.validate_startable()
        await self.nova_client.start_server(
            client=client, keystone_token=keystone_token, server_openstack_id=server.openstack_id
        )

        return ServerResponse.from_entity(server)

    @transactional()
    async def stop_server(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        server_id: int,
    ) -> ServerResponse:
        server: Server = await self._get_server_by_id(session=session, server_id=server_id)
        server.validate_access_permission(project_id=project_id)
        server.validate_stoppable()
        await self.nova_client.stop_server(
            client=client, keystone_token=keystone_token, server_openstack_id=server.openstack_id
        )

        return ServerResponse.from_entity(server)

    @transactional()
    async def wait_until_server_started(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
    ) -> bool:
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE)

            os_server: OsServerDto = await self.nova_client.get_server(
                client=client,
                keystone_token=keystone_token,
                server_openstack_id=server_openstack_id,
            )

            if os_server.status == ServerStatus.SHUTOFF or os_server.status == ServerStatus.ERROR:
                continue

            if os_server.status == ServerStatus.ACTIVE:
                server: Server = await self._get_server_by_openstack_id(
                    session=session, openstack_id=server_openstack_id
                )
                server.start()
                return True
            logger.error(f"서버({server_openstack_id}) 시작 도중 에러가 발생했습니다. status={os_server.status}")
            return False

        logger.error(
            f"서버({server_openstack_id}) 시작을 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE}초 동안 "
            f"정상적으로 시작되지 않았습니다."
        )
        return False

    @transactional()
    async def wait_until_server_stopped(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
    ) -> bool:
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE)

            os_server: OsServerDto = await self.nova_client.get_server(
                client=client,
                keystone_token=keystone_token,
                server_openstack_id=server_openstack_id,
            )

            if os_server.status == ServerStatus.ACTIVE:
                continue
            if os_server.status == ServerStatus.SHUTOFF:
                server: Server = await self._get_server_by_openstack_id(
                    session=session, openstack_id=server_openstack_id
                )
                server.stop()
                return True
            logger.error(f"서버({server_openstack_id}) 중지 도중 에러가 발생했습니다. status={os_server.status}")
            return False

        logger.error(
            f"서버({server_openstack_id}) 중지를 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE}초 동안 "
            f"정상적으로 중지되지 않았습니다."
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

    async def _get_server_by_openstack_id(
        self,
        session: AsyncSession,
        openstack_id: str,
        with_deleted: bool = False,
    ):
        if (server := await self.server_repository.find_by_openstack_id(
            session=session, openstack_id=openstack_id, with_deleted=with_deleted
        )) is None:
            raise ServerNotFoundException()
        return server
