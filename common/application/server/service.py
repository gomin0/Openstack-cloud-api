from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.response import ServerDetailsResponse, ServerDetailResponse
from common.domain.enum import SortOrder
from common.domain.server.enum import ServerSortOption
from common.exception.server_exception import ServerNotFoundException
from common.infrastructure.server.repository import ServerRepository


class ServerService:
    def __init__(self, server_repository: ServerRepository = Depends()):
        self.server_repository = server_repository

    async def find_servers_details(
        self,
        session: AsyncSession,
        ids: list[int] | None,
        is_exclude_ids: bool,
        name: str | None,
        name_like: str | None,
        sort_by: ServerSortOption,
        order: SortOrder,
        project_id: int,
        with_deleted: bool = False,
    ) -> ServerDetailsResponse:
        servers = await self.server_repository.find_all_by_project_id(
            session=session,
            ids=ids,
            is_exclude_ids=is_exclude_ids,
            name=name,
            name_like=name_like,
            sort_by=sort_by,
            order=order,
            project_id=project_id,
            with_deleted=with_deleted,
            with_relations=True,
        )
        return ServerDetailsResponse(
            servers=[await ServerDetailResponse.from_entity(server) for server in servers]
        )

    async def get_server_detail(
        self,
        session: AsyncSession,
        server_id: int,
        project_id: int,
        with_deleted: bool = False,
    ) -> ServerDetailResponse:
        server = await self.server_repository.find_by_id(
            session=session,
            server_id=server_id,
            with_deleted=with_deleted,
            with_relations=True,
        )
        if not server:
            raise ServerNotFoundException()
        server.validate_access_permission(project_id=project_id)

        return await ServerDetailResponse.from_entity(server)
