from sqlalchemy import select, exists, Select

from common.domain.security_group.entity import NetworkInterfaceSecurityGroup
from common.infrastructure.database import session_factory


class NetworkInterfaceSecurityGroupRepository:
    async def exists_by_security_group(self, security_group_id: int) -> bool:
        async with session_factory() as session:
            query: Select[tuple[bool]] = select(exists().where(
                NetworkInterfaceSecurityGroup.security_group_id == security_group_id,
            ))
            return await session.scalar(query)
