from datetime import datetime

from sqlalchemy import select, Select, ScalarResult, exists
from sqlalchemy.orm import selectinload, InstrumentedAttribute

from common.domain.enum import SortOrder
from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.entity import NetworkInterfaceSecurityGroup
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.infrastructure.database import session_factory


class ServerRepository:
    async def find_all_by_project_id(
        self,
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
        async with session_factory() as session:
            query: Select[tuple[Server]] = select(Server).where(Server.project_id == project_id)

            if not with_deleted:
                query = query.where(Server.deleted_at.is_(None))
            if with_relations:
                query = query.options(
                    selectinload(Server._linked_volumes),

                    selectinload(Server._linked_network_interfaces).joinedload(NetworkInterface._floating_ip),

                    selectinload(Server._linked_network_interfaces)
                    .selectinload(NetworkInterface._linked_security_groups)
                    .joinedload(NetworkInterfaceSecurityGroup._security_group),
                )
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
        server_id: int,
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> Server | None:
        async with session_factory() as session:
            query: Select[tuple[Server]] = select(Server).where(Server.id == server_id)
            if not with_deleted:
                query = query.where(Server.deleted_at.is_(None))
            if with_relations:
                query = query.options(
                    selectinload(Server._linked_volumes),

                    selectinload(Server._linked_network_interfaces).joinedload(NetworkInterface._floating_ip),

                    selectinload(Server._linked_network_interfaces)
                    .selectinload(NetworkInterface._linked_security_groups)
                    .joinedload(NetworkInterfaceSecurityGroup._security_group),
                )
            return await session.scalar(query)

    async def find_by_openstack_id(
        self,
        openstack_id: str,
        with_deleted: bool = False,
    ) -> Server | None:
        async with session_factory() as session:
            query: Select = select(Server).where(Server.openstack_id == openstack_id)
            if not with_deleted:
                query = query.where(Server.deleted_at.is_(None))
            return await session.scalar(query)

    async def find_by_openstack_id(
        self,
        openstack_id: str,
        with_deleted: bool = False,
    ) -> Server | None:
        async with session_factory() as session:
            query: Select = select(Server).where(Server.openstack_id == openstack_id)
            if not with_deleted:
                query = query.where(Server.deleted_at.is_(None))
            return await session.scalar(query)

    async def find_by_openstack_id(
        self,
        openstack_id: str,
        with_deleted: bool = False,
    ) -> Server | None:
        async with session_factory() as session:
            query: Select = select(Server).where(Server.openstack_id == openstack_id)
            if not with_deleted:
                query = query.where(Server.deleted_at.is_(None))
            return await session.scalar(query)

    async def exists_by_project_and_name(self, project_id: int, name: str) -> bool:
        async with session_factory() as session:
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

    async def create(self, server: Server) -> Server:
        async with session_factory() as session:
            session.add(server)
            await session.flush()
            return server
