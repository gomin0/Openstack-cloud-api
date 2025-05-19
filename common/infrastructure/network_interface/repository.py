from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.domain.network_interface.entity import NetworkInterface


class NetworkInterfaceRepository:
    async def find_by_id(
        self,
        session: AsyncSession,
        network_interface_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> NetworkInterface | None:
        query: Select = select(NetworkInterface).where(NetworkInterface.id == network_interface_id)

        if not with_deleted:
            query = query.where(NetworkInterface.deleted_at.is_(None))

        if with_relations:
            query = query.options(selectinload(NetworkInterface._server))

        result: NetworkInterface | None = await session.scalar(query)

        return result

    async def create(self, session: AsyncSession, network_interface: NetworkInterface):
        session.add(network_interface)
        await session.flush()
        return network_interface
