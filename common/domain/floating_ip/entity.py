from datetime import timezone, datetime

from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.floating_ip.enum import FloatingIpStatus
from common.domain.server.entity import Server


class FloatingIp(SoftDeleteBaseEntity):
    __tablename__ = "floating_ip"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    server_id: Mapped[int | None] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=True)
    status: Mapped[FloatingIpStatus] = mapped_column(
        Enum(FloatingIpStatus, name="status", native_enum=False, length=30),
        nullable=False
    )
    address: Mapped[str] = mapped_column("address", String(15), nullable=False)

    _server: Mapped[Server] = relationship("Server", lazy="select")

    @async_property
    async def server(self) -> Server:
        return await self.awaitable_attrs._server

    @classmethod
    def create(
        cls,
        openstack_id: str,
        project_id: int,
        address: str,
    ) -> "FloatingIp":
        return cls(
            id=None,
            openstack_id=openstack_id,
            project_id=project_id,
            server_id=None,
            status=FloatingIpStatus.DOWN,
            address=address,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
