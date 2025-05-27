from sqlalchemy import select, ScalarResult, Select, exists
from sqlalchemy.orm import selectinload

from common.domain.enum import SortOrder
from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.entity import SecurityGroup, NetworkInterfaceSecurityGroup
from common.domain.security_group.enum import SecurityGroupSortOption
from common.infrastructure.database import session_factory


class SecurityGroupRepository:
    async def find_all_by_ids(
        self,
        ids: list[int],
        with_deleted: bool = False,
    ) -> list[SecurityGroup]:
        async with session_factory() as session:
            query: Select = select(SecurityGroup).where(SecurityGroup.id.in_(ids))
            if not with_deleted:
                query = query.where(SecurityGroup.deleted_at.is_(None))
            result: ScalarResult = await session.scalars(query)
            return result.all()

    async def find_all_by_project_id(
        self,
        project_id: int,
        sort_by: SecurityGroupSortOption = SecurityGroupSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> list[SecurityGroup]:
        async with session_factory() as session:
            query: Select[tuple[SecurityGroup]] = select(SecurityGroup).where(
                SecurityGroup.project_id == project_id
            )

            if not with_deleted:
                query = query.where(SecurityGroup.deleted_at.is_(None))

            if with_relations:
                query = query.options(
                    selectinload(SecurityGroup._linked_network_interfaces)
                    .joinedload(NetworkInterfaceSecurityGroup._network_interface)
                    .joinedload(NetworkInterface._server)
                )

            order_by_column = {
                SecurityGroupSortOption.NAME: SecurityGroup.name,
                SecurityGroupSortOption.CREATED_AT: SecurityGroup.created_at
            }.get(sort_by, SecurityGroup.created_at)

            if order == SortOrder.DESC:
                order_by_column = order_by_column.desc()

            query = query.order_by(order_by_column)

            result: ScalarResult[SecurityGroup] = await session.scalars(query)
            return result.all()

    async def find_by_id(
        self,
        security_group_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> SecurityGroup | None:
        async with session_factory() as session:
            query = select(SecurityGroup).where(SecurityGroup.id == security_group_id)

            if not with_deleted:
                query = query.where(SecurityGroup.deleted_at.is_(None))

            if with_relations:
                query = query.options(
                    selectinload(SecurityGroup._linked_network_interfaces)
                    .joinedload(NetworkInterfaceSecurityGroup._network_interface)
                    .joinedload(NetworkInterface._server)
                )

            return await session.scalar(query)

    async def exists_by_project_and_name(
        self,
        project_id: int,
        name: str,
    ) -> bool:
        async with session_factory() as session:
            result: bool = await session.scalar(
                select(exists().where(
                    SecurityGroup.project_id == project_id,
                    SecurityGroup.name == name,
                    SecurityGroup.deleted_at.is_(None)
                ))
            )
            return result

    async def create(self, security_group: SecurityGroup) -> SecurityGroup:
        async with session_factory() as session:
            session.add(security_group)
            await session.flush()

            return security_group
