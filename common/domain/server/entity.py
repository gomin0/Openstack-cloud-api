from async_property import async_property
from sqlalchemy import CHAR, BigInteger, ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.server.enum import ServerStatus
from common.exception.server_exception import ServerAccessDeniedException


class Server(SoftDeleteBaseEntity):
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

    _floating_ip: Mapped["FloatingIp"] = relationship("FloatingIp", lazy="select")
    _linked_volumes: Mapped[list["Volume"]] = relationship("Volume", lazy="select")
    _linked_network_interface: Mapped[list["NetworkInterface"]] = relationship("NetworkInterface", lazy="select")
    _linked_security_groups: Mapped[list["ServerSecurityGroup"]] = relationship(
        "ServerSecurityGroup",
        lazy="select",
        back_populates="_server"
    )

    @async_property
    async def security_groups(self) -> list["SecurityGroup"]:
        linked_security_group: list["SecurityGroup"] = await self.awaitable_attrs._linked_security_groups
        return [await link.security_group for link in linked_security_group]

    @async_property
    async def volumes(self) -> list["Volume"]:
        return await self.awaitable_attrs._linked_volumes

    @async_property
    async def floating_ip(self) -> "FloatingIp":
        return await self.awaitable_attrs._floating_ip

    @async_property
    async def network_interfaces(self) -> list["NetworkInterface"]:
        return await self.awaitable_attrs._linked_network_interface

    def validate_access_permission(self, project_id):
        if self.project_id != project_id:
            raise ServerAccessDeniedException()
