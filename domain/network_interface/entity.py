from datetime import datetime, timezone

from sqlalchemy import BigInteger, CHAR, ForeignKey, Enum, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from domain.entity import Base
from domain.enum import LifecycleStatus


class NetworkInterface(Base):
    __tablename__ = "network_interface"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    server_id: Mapped[int | None] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=True)
    port_openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    fixed_ip_address: Mapped[str] = mapped_column("fixed_ip_address", String(15), nullable=False)
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
