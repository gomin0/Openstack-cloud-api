from datetime import datetime

from sqlalchemy import select, Select, ScalarResult, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, InstrumentedAttribute

from common.domain.enum import SortOrder
from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.entity import NetworkInterfaceSecurityGroup
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption


class ServerRepository:
    async def find_all_by_project_id(
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
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> list[Server]:
        query: Select[tuple[Server]] = select(Server).where(Server.project_id == project_id)

        if not with_deleted:
            query = query.where(Server.deleted_at.is_(None))
        if with_relations:
            query = query.options(*self._with_relations())
        if id_:
            query = query.where(Server.id == id_)
        if ids_contain:
            query = query.where(Server.id.in_(ids_contain))
        if ids_exclude:
            query = query.where(Server.id.not_in(ids_exclude))
        if name_eq:
            query = query.where(Server.name == name_eq)
        if name_like:
            query = query.where(Server.name.like(f"%{name_like}%"))

        order_column: InstrumentedAttribute[str] | InstrumentedAttribute[datetime] = {
            ServerSortOption.NAME: Server.name,
            ServerSortOption.CREATED_AT: Server.created_at
        }.get(sort_by, Server.created_at)

        if order == SortOrder.DESC:
            order_column = order_column.desc()

        query: Select[tuple[Server]] = query.order_by(order_column)
        result: ScalarResult[Server] = await session.scalars(query)

        return result.all()

    async def find_by_id(
        self,
        session: AsyncSession,
        server_id: int,
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> Server | None:
        query: Select[tuple[Server]] = select(Server).where(Server.id == server_id)

        if not with_deleted:
            query = query.where(Server.deleted_at.is_(None))
        if with_relations:
            query = query.options(*self._with_relations())

        return await session.scalar(query)

    async def exists_by_project_and_name(self, session: AsyncSession, project_id: int, name: str) -> bool:
        return await session.scalar(
            select(
                exists()
                .where(
                    Server.deleted_at.is_(None),
                    Server.project_id == project_id,
                    Server.name == name,
                )
            )
        )

    def _with_relations(self):
        return (
            selectinload(Server._linked_volumes),

            selectinload(Server._linked_network_interfaces).joinedload(NetworkInterface._floating_ip),

            selectinload(Server._linked_network_interfaces)
            .selectinload(NetworkInterface._linked_security_groups)
            .joinedload(NetworkInterfaceSecurityGroup._security_group),
        )
