from datetime import datetime, timezone

from sqlalchemy import CHAR, BigInteger, ForeignKey, String, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.entity import Base
from domain.enum import LifecycleStatus
from domain.server.enum import ServerStatus


class Server(Base):
    __tablename__ = "server"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    flavor_openstack_id: Mapped[str] = mapped_column("flavor_openstack_id", CHAR(36), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    description: Mapped[str] = mapped_column("description", String(255), nullable=False)
    status: Mapped[ServerStatus] = mapped_column(
        Enum(ServerStatus, name="status", native_enum=False, length=30),
        nullable=False
    )
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

    _linked_security_groups: Mapped[list["ServerSecurityGroup"]] = relationship(
        "ServerSecurityGroup",
        lazy="select",
        back_populates="_server"
    )
