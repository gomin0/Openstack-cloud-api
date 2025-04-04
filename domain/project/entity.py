from datetime import datetime, timezone

from async_property import async_property
from sqlalchemy import String, DateTime, ForeignKey, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.domain.entity import Domain
from domain.entity import Base
from domain.enum import EntityStatus
from domain.user.entitiy import User


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    domain_id: Mapped[int] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        "status", String(15), nullable=False, default=EntityStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)

    _domain: Mapped[Domain] = relationship("Domain", lazy="select")
    _linked_users: Mapped[list["ProjectUser"]] = relationship("ProjectUser", lazy="select")

    @async_property
    async def domain(self) -> Domain:
        return await self.awaitable_attrs._domain

    @async_property
    async def users(self) -> list[User]:
        linked_users = await self.awaitable_attrs._linked_users
        return [await link.awaitable_attrs.user for link in linked_users]


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

    _user: Mapped[User] = relationship("User", lazy="select")

    @async_property
    async def user(self) -> User:
        return await self.awaitable_attrs._user
