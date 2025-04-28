from sqlalchemy import select, Select, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from domain.enum import SortOrder, LifecycleStatus
from domain.floating_ip.entity import FloatingIp
from domain.floating_ip.enum import FloatingIpSortOption


class FloatingIpRepository:
    async def find_all_by_project_id(
        self,
        session: AsyncSession,
        project_id: int,
        sort_by: FloatingIpSortOption = FloatingIpSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> list[FloatingIp]:
        query: Select[tuple[FloatingIp]] = select(FloatingIp).where(
            FloatingIp.project_id == project_id
        )

        if not with_deleted:
            query = query.where(FloatingIp.lifecycle_status == LifecycleStatus.ACTIVE)

        if with_relations:
            query = query.options(
                joinedload(FloatingIp._server)
            )

        order_by_column = {
            FloatingIpSortOption.ADDRESS: FloatingIp.address,
            FloatingIpSortOption.CREATED_AT: FloatingIp.created_at
        }.get(sort_by, FloatingIp.created_at)
        if order == SortOrder.DESC:
            order_by_column = order_by_column.desc()
        query = query.order_by(order_by_column)

        result: ScalarResult[FloatingIp] = await session.scalars(query)

        return result.all()
