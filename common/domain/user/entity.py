from async_property import async_property
from sqlalchemy import String, ForeignKey, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.domain.entity import Domain
from common.domain.entity import SoftDeleteBaseEntity


class User(SoftDeleteBaseEntity):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    domain_id: Mapped[int] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    account_id: Mapped[str] = mapped_column("account_id", String(20), nullable=False)
    name: Mapped[str] = mapped_column("name", String(15), nullable=False)
    password: Mapped[str] = mapped_column("password", String(255), nullable=False)

    _domain: Mapped[Domain] = relationship("Domain", lazy="select")
    _linked_projects: Mapped[list["ProjectUser"]] = relationship("ProjectUser", lazy="select", back_populates="_user")

    @async_property
    async def domain(self) -> Domain:
        return await self.awaitable_attrs._domain

    @async_property
    async def projects(self) -> list["Project"]:
        linked_projects: list["ProjectUser"] = await self.awaitable_attrs._linked_projects
        return [await link.project for link in linked_projects]

    @classmethod
    def create(
        cls,
        openstack_id: str,
        domain_id: int,
        account_id: str,
        name: str,
        hashed_password: str,
    ) -> "User":
        return cls(
            openstack_id=openstack_id,
            domain_id=domain_id,
            account_id=account_id,
            name=name,
            password=hashed_password,
        )

    def update_info(self, name: str):
        self.name = name
