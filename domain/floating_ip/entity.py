from datetime import datetime, timezone

from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.entity import Base
from domain.enum import LifecycleStatus
from domain.floating_ip.enum import FloatingIpStatus
from domain.server.entity import Server


class FloatingIp(Base):
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
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status", native_enum=False, length=15),
        nullable=False,
        default=LifecycleStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)

    _server: Mapped[Server] = relationship("Server", lazy="select")

    @async_property
    async def server(self) -> Server:
        return await self.awaitable_attrs._server
