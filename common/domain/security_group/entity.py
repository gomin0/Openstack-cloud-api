from datetime import datetime, timezone

from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from common.domain.entity import SoftDeleteBaseEntity, BaseEntity
from common.domain.server.entity import Server


class SecurityGroup(SoftDeleteBaseEntity):
    __tablename__ = "security_group"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    description: Mapped[str | None] = mapped_column("description", String(255), nullable=True)

    _linked_servers: Mapped[list[Server]] = relationship(
        "ServerSecurityGroup", lazy="select", back_populates="_security_group"
    )

    @async_property
    async def servers(self) -> list[Server]:
        linked_servers: list[ServerSecurityGroup] = await self.awaitable_attrs._linked_servers
        return [await link.server for link in linked_servers]

    @classmethod
    def create(
        cls,
        openstack_id: str,
        project_id: int,
        name: str,
        description: str | None,
    ) -> "SecurityGroup":
        return cls(
            id=None,
            openstack_id=openstack_id,
            project_id=project_id,
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )


class ServerSecurityGroup(BaseEntity):
    __tablename__ = "server_security_group"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=False)
    security_group_id: Mapped[int] = mapped_column(
        "security_group_id",
        BigInteger,
        ForeignKey("security_group.id"),
        nullable=False
    )

    _server: Mapped[Server] = relationship("Server", lazy="select", back_populates="_linked_security_groups")
    _security_group: Mapped["SecurityGroup"] = relationship("SecurityGroup", lazy="select",
                                                            back_populates="_linked_servers")

    @async_property
    async def server(self) -> Server:
        return await self.awaitable_attrs._server

    @async_property
    async def security_group(self) -> SecurityGroup:
        return await self.awaitable_attrs._security_group
