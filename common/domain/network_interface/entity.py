from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.server.entity import Server
from common.exception.network_interface_exception import NetworkInterfaceAccessPermissionDeniedException


class NetworkInterface(SoftDeleteBaseEntity):
    __tablename__ = "network_interface"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    server_id: Mapped[int | None] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=True)
    fixed_ip_address: Mapped[str] = mapped_column("fixed_ip_address", String(15), nullable=False)

    _server: Mapped[Server | None] = relationship("Server", lazy="select", back_populates="_linked_network_interfaces")
    _floating_ip: Mapped["FloatingIp"] = relationship("FloatingIp", lazy="select", back_populates="_network_interface")
    _linked_security_groups: Mapped[list["NetworkInterfaceSecurityGroup"]] = relationship(
        "NetworkInterfaceSecurityGroup",
        lazy="select",
        back_populates="_network_interface",
        cascade="save-update, merge, delete-orphan",
    )

    @async_property
    async def server(self) -> Server | None:
        return await self.awaitable_attrs._server

    @async_property
    async def floating_ip(self) -> "FloatingIp":
        return await self.awaitable_attrs._floating_ip

    @async_property
    async def security_groups(self) -> list["SecurityGroup"]:
        linked_security_groups: list["NetworkInterfaceSecurityGroup"] = \
            await self.awaitable_attrs._linked_security_groups
        return [await link.security_group for link in linked_security_groups]

    def validate_access_permission(self, project_id):
        if self.project_id != project_id:
            raise NetworkInterfaceAccessPermissionDeniedException()

    async def detach_all_security_groups(self):
        security_groups: list["SecurityGroup"] = await self.awaitable_attrs._linked_security_groups
        security_groups.clear()
