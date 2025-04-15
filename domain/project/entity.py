from datetime import datetime, timezone

from async_property import async_property
from sqlalchemy import String, DateTime, ForeignKey, BigInteger, CHAR, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.domain.entity import Domain
from domain.entity import Base
from domain.enum import LifecycleStatus
from domain.user.entity import User


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    domain_id: Mapped[int] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
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
    version: Mapped[int] = mapped_column("version", Integer, nullable=False, default=0)

    _domain: Mapped[Domain] = relationship("Domain", lazy="select")
    _linked_users: Mapped[list["ProjectUser"]] = relationship("ProjectUser", lazy="select", back_populates="_project")

    @async_property
    async def domain(self) -> Domain:
        return await self.awaitable_attrs._domain

    @async_property
    async def users(self) -> list[User]:
        linked_users: list[ProjectUser] = await self.awaitable_attrs._linked_users
        return [await link.user for link in linked_users]

    __mapper_args__ = {"version_id_col": version}

    def update_name(self, name: str) -> None:
        self.name = name


class ProjectUser(Base):
    __tablename__ = "project_user"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("user.id"), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    role_id: Mapped[str] = mapped_column("role_id", CHAR(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    _user: Mapped[User] = relationship("User", lazy="select", back_populates="_linked_projects")
    _project: Mapped[Project] = relationship("Project", lazy="select", back_populates="_linked_users")

    @async_property
    async def user(self) -> User:
        return await self.awaitable_attrs._user

    @async_property
    async def project(self) -> Project:
        return await self.awaitable_attrs._project
