from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.response import ServerDetailsResponse, ServerDetailResponse
from common.domain.enum import SortOrder
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.exception.server_exception import ServerNotFoundException
from common.infrastructure.database import transactional
from common.infrastructure.nova.client import NovaClient
from common.infrastructure.server.repository import ServerRepository


class ServerService:
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
        servers = await self.server_repository.find_all_by_project_id(
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
        return ServerDetailsResponse(
            servers=[await ServerDetailResponse.from_entity(server) for server in servers]
        )

    @transactional()
    async def get_server_detail(
        self,
        session: AsyncSession,
        server_id: int,
        project_id: int,
    ) -> ServerDetailResponse:
        server = await self.server_repository.find_by_id(
            session=session,
            server_id=server_id,
            with_relations=True,
        )
        if not server:
            raise ServerNotFoundException()
        server.validate_access_permission(project_id=project_id)

        return await ServerDetailResponse.from_entity(server)

    async def get_server_vnc_url(
        self,
        session: AsyncSession,
        client: AsyncClient,
        server_id: int,
        project_id: int,
        keystone_token: str,
    ) -> str:
        server: Server = await self._get_server_by_id(
            session=session,
            server_id=server_id
        )
        server.validate_access_permission(project_id=project_id)

        vnc_url: str = await self.nova_client.get_vnc_console(
            client=client,
            keystone_token=keystone_token,
            server_openstack_id=server.openstack_id
        )

        return vnc_url

    @transactional()
    async def _get_server_by_id(
        self,
        session: AsyncSession,
        server_id: int,
        with_deleted: bool,
        with_relations: bool,
    ) -> Server | None:
        if server := await self.server_repository.find_by_id(
            session=session,
            server_id=server_id,
            with_deleted=with_deleted,
            with_relations=with_relations,
        ) is None:
            raise ServerNotFoundException()

        return server
