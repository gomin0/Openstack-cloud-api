from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity


class NetworkInterface(SoftDeleteBaseEntity):
    __tablename__ = "network_interface"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    server_id: Mapped[int | None] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    fixed_ip_address: Mapped[str] = mapped_column("fixed_ip_address", String(15), nullable=False)

    _server: Mapped["Server"] = relationship("Server", lazy="select")
    _floating_ip: Mapped["FloatingIp"] = relationship("FloatingIp", lazy="select")

    @async_property
    async def server(self) -> "Server":
        return await self.awaitable_attrs._server

    @async_property
    async def floating_ip(self) -> "FloatingIp":
        return await self.awaitable_attrs._floating_ip
