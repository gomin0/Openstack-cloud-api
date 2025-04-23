from sqlalchemy import select, ScalarResult, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.enum import LifecycleStatus
from domain.enum import SortOrder
from domain.security_group.entity import SecurityGroup, ServerSecurityGroup
from domain.security_group.enum import SecurityGroupSortOption


class SecurityGroupRepository:
    async def find_all_by_project_id(
        self,
        session: AsyncSession,
        project_id: int,
        sort_by: SecurityGroupSortOption = SecurityGroupSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
    ) -> list[SecurityGroup] | None:
        query: Select[tuple[SecurityGroup]] = select(SecurityGroup).where(
            SecurityGroup.project_id == project_id
        )

        if not with_deleted:
            query = query.where(SecurityGroup.lifecycle_status == LifecycleStatus.ACTIVE)

        query = query.options(
            selectinload(SecurityGroup._linked_servers)
            .selectinload(ServerSecurityGroup._server)
        )

        order_by_column = {
            SecurityGroupSortOption.NAME: SecurityGroup.name,
            SecurityGroupSortOption.CREATED_AT: SecurityGroup.created_at
        }.get(sort_by, SecurityGroup.created_at)

        if order == SortOrder.DESC:
            order_by_column = order_by_column.desc()

        query = query.order_by(order_by_column)

        result: ScalarResult[SecurityGroup] = await session.scalars(query)
        return list(result.all())
