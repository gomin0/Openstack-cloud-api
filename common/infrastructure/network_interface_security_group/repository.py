from sqlalchemy import select, exists, Select, delete, Delete
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.security_group.entity import NetworkInterfaceSecurityGroup


class NetworkInterfaceSecurityGroupRepository:
    async def exists_by_security_group(
        self,
        session: AsyncSession,
        security_group_id: int,
    ) -> bool:
        query: Select[tuple[bool]] = select(exists().where(
            NetworkInterfaceSecurityGroup.security_group_id == security_group_id,
        ))

        return await session.scalar(query)

    async def delete_all_by_network_interface(
        self,
        session: AsyncSession,
        network_interface_id: int,
    ) -> None:
        query: Delete = delete(NetworkInterfaceSecurityGroup).where(
            NetworkInterfaceSecurityGroup.network_interface_id == network_interface_id
        )
        await session.execute(query)
