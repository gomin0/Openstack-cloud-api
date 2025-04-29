from sqlalchemy import select, ScalarResult, Select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.domain.enum import LifecycleStatus
from common.domain.enum import SortOrder
from common.domain.security_group.entity import SecurityGroup, ServerSecurityGroup
from common.domain.security_group.enum import SecurityGroupSortOption


class SecurityGroupRepository:
    async def find_all_by_project_id(
        self,
        session: AsyncSession,
        project_id: int,
        sort_by: SecurityGroupSortOption = SecurityGroupSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> list[SecurityGroup]:
        query: Select[tuple[SecurityGroup]] = select(SecurityGroup).where(
            SecurityGroup.project_id == project_id
        )

        if not with_deleted:
            query = query.where(SecurityGroup.lifecycle_status == LifecycleStatus.ACTIVE)

        if with_relations:
            query = query.options(self._with_relations())

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
        session: AsyncSession,
        security_group_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> SecurityGroup | None:
        query = select(SecurityGroup).where(SecurityGroup.id == security_group_id)

        if not with_deleted:
            query = query.where(
                SecurityGroup.lifecycle_status == LifecycleStatus.ACTIVE
            )

        if with_relations:
            query = query.options(self._with_relations())

        return await session.scalar(query)

    @staticmethod
    def _with_relations():
        return selectinload(SecurityGroup._linked_servers).selectinload(ServerSecurityGroup._server)

    async def exists_by_project_and_name(
        self,
        session: AsyncSession,
        project_id: int,
        name: str,
    ) -> bool:
        result: bool = await session.scalar(
            select(exists().where(
                SecurityGroup.project_id == project_id,
                SecurityGroup.name == name,
                SecurityGroup.lifecycle_status == LifecycleStatus.ACTIVE
            ))
        )
        return result

    async def create(
        self,
        session: AsyncSession,
        security_group: SecurityGroup,
    ) -> SecurityGroup:
        session.add(security_group)
        await session.flush()

        return security_group
