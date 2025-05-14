from sqlalchemy import select, ScalarResult, Select
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.network_interface.entity import NetworkInterface


class NetworkInterfaceRepository:
    async def find_by_ids(
        self,
        session: AsyncSession,
        network_interface_ids: list[int],
    ) -> list[NetworkInterface]:
        query: Select = select(NetworkInterface).filter(
            NetworkInterface.id.in_(network_interface_ids),
            NetworkInterface.deleted_at.is_(None)
        )
        result: ScalarResult = await session.scalars(query)
        return result.all()
