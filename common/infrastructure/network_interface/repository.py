from sqlalchemy import select, Select, ScalarResult
from sqlalchemy.orm import selectinload

from common.domain.network_interface.entity import NetworkInterface
from common.infrastructure.database import session_factory


class NetworkInterfaceRepository:
    async def find_by_id(
        self,
        network_interface_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> NetworkInterface | None:
        async with session_factory() as session:
            query: Select = select(NetworkInterface).where(NetworkInterface.id == network_interface_id)

            if not with_deleted:
                query = query.where(NetworkInterface.deleted_at.is_(None))

            if with_relations:
                query = query.options(selectinload(NetworkInterface._server))

            result: NetworkInterface | None = await session.scalar(query)

            return result

    async def find_all_by_ids(self, network_interface_ids: list[int]) -> list[NetworkInterface]:
        async with session_factory() as session:
            query: Select = select(NetworkInterface).where(
                NetworkInterface.id.in_(network_interface_ids),
                NetworkInterface.deleted_at.is_(None)
            )
            result: ScalarResult = await session.scalars(query)
            return result.all()

    async def create(self, network_interface: NetworkInterface):
        async with session_factory() as session:
            session.add(network_interface)
            await session.flush()
            return network_interface
