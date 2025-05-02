from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.security_group.entity import ServerSecurityGroup


class ServerSecurityGroupRepository:
    async def exists_by_security_group(
        self,
        session: AsyncSession,
        security_group_id: int,
    ) -> bool:
        query = select(exists().where(
            ServerSecurityGroup.security_group_id == security_group_id,
        ))
        result = await session.scalar(query)

        return result
