from sqlalchemy.ext.asyncio import AsyncSession

from domain.floating_ip.entity import FloatingIp


class FloatingIpRepository:
    async def create(
        self,
        session: AsyncSession,
        floating_ip: FloatingIp
    ) -> FloatingIp:
        session.add(floating_ip)
        await session.flush()
        return floating_ip
