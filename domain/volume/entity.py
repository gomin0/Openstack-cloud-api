from datetime import datetime, timezone

from sqlalchemy import BigInteger, CHAR, ForeignKey, String, Integer, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from domain.entity import Base
from domain.enum import LifecycleStatus
from domain.volume.enum import VolumeStatus


class Volume(Base):
    __tablename__ = "volume"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    server_id: Mapped[int | None] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=True)
    volume_type_openstack_id: Mapped[str] = mapped_column("volume_type_openstack_id", CHAR(36), nullable=False)
    image_openstack_id: Mapped[str | None] = mapped_column("image_openstack_id", CHAR(36), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    description: Mapped[str] = mapped_column("description", String(255), nullable=False)
    status: Mapped[VolumeStatus] = mapped_column(
        Enum(VolumeStatus, name="status", native_enum=False, length=30),
        nullable=False
    )
    size: Mapped[int] = mapped_column("size", Integer, nullable=False)
    is_root_volume: Mapped[bool] = mapped_column("is_root_volume", Boolean, nullable=False)
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status", native_enum=False, length=15),
        nullable=False,
        default=LifecycleStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)
