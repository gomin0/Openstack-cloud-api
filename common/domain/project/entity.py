from async_property import async_property
from sqlalchemy import String, ForeignKey, BigInteger, CHAR, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.domain.entity import Domain
from common.domain.entity import BaseEntity, SoftDeleteBaseEntity
from common.domain.user.entity import User


class Project(SoftDeleteBaseEntity):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    domain_id: Mapped[int] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    version: Mapped[int] = mapped_column("version", Integer, nullable=False, default=0)

    _domain: Mapped[Domain] = relationship("Domain", lazy="select")
    _linked_users: Mapped[list["ProjectUser"]] = relationship(
        "ProjectUser",
        lazy="select",
        back_populates="_project",
        cascade="save-update, merge, delete, delete-orphan",
    )

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


class ProjectUser(BaseEntity):
    __tablename__ = "project_user"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("user.id"), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)

    _user: Mapped[User] = relationship("User", lazy="select", back_populates="_linked_projects")
    _project: Mapped[Project] = relationship("Project", lazy="select", back_populates="_linked_users")

    @async_property
    async def user(self) -> User:
        return await self.awaitable_attrs._user

    @async_property
    async def project(self) -> Project:
        return await self.awaitable_attrs._project
