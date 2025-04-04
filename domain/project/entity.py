from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.domain.entity import Domain
from domain.enum import EntityStatus
from infrastructure.database import Base


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    domain_id: Mapped[str] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        "status", String(15), nullable=False, default=EntityStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)

    domain: Mapped[Domain] = relationship("Domain", lazy="select")


class ProjectUser(Base):
    __tablename__ = "project_user"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column("user_id", BigInteger, ForeignKey("user.id"), nullable=False)
    project_id: Mapped[str] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    role_id: Mapped[str] = mapped_column("role_id", CHAR(32), ForeignKey("role.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now(timezone.utc)
    )
