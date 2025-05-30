from sqlalchemy import select, Select, ScalarResult
from sqlalchemy.orm import joinedload

from common.domain.enum import SortOrder
from common.domain.floating_ip.entity import FloatingIp
from common.domain.floating_ip.enum import FloatingIpSortOption
from common.domain.network_interface.entity import NetworkInterface
from common.infrastructure.database import session_factory


class FloatingIpRepository:
    async def find_all_by_project_id(
        self,
        project_id: int,
        sort_by: FloatingIpSortOption = FloatingIpSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> list[FloatingIp]:
        async with session_factory() as session:
            query: Select[tuple[FloatingIp]] = select(FloatingIp).where(
                FloatingIp.project_id == project_id
            )

            if not with_deleted:
                query = query.where(FloatingIp.deleted_at.is_(None))

            if with_relations:
                query = query.options(joinedload(FloatingIp._network_interface).joinedload(NetworkInterface._server))

            order_by_column = {
                FloatingIpSortOption.ADDRESS: FloatingIp.address,
                FloatingIpSortOption.CREATED_AT: FloatingIp.created_at
            }.get(sort_by, FloatingIp.created_at)
            if order == SortOrder.DESC:
                order_by_column = order_by_column.desc()
            query = query.order_by(order_by_column)

            result: ScalarResult[FloatingIp] = await session.scalars(query)

            return result.all()

    async def find_by_id(
        self,
        floating_ip_id: int,
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> FloatingIp | None:
        async with session_factory() as session:
            query: Select[tuple[FloatingIp]] = select(FloatingIp).where(FloatingIp.id == floating_ip_id)

            if not with_deleted:
                query = query.where(
                    FloatingIp.deleted_at.is_(None)
                )

            if with_relations:
                query = query.options(joinedload(FloatingIp._network_interface).joinedload(NetworkInterface._server))

            result: FloatingIp | None = await session.scalar(query)

            return result

    async def create(self, floating_ip: FloatingIp) -> FloatingIp:
        async with session_factory() as session:
            session.add(floating_ip)
            await session.flush()
            return floating_ip
