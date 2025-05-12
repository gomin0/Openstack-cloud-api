from sqlalchemy import select, exists, Select
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.security_group.entity import ServerSecurityGroup


class ServerSecurityGroupRepository:
    async def exists_by_security_group(
        self,
        session: AsyncSession,
        security_group_id: int,
    ) -> bool:
        query: Select[tuple[bool]] = select(exists().where(
            ServerSecurityGroup.security_group_id == security_group_id,
        ))

        return await session.scalar(query)
