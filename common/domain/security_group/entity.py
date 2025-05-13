from datetime import datetime, timezone

from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity, BaseEntity
from common.domain.network_interface.entity import NetworkInterface
from common.domain.server.entity import Server
from common.exception.security_group_exception import SecurityGroupDeletePermissionDeniedException, \
    SecurityGroupUpdatePermissionDeniedException


class SecurityGroup(SoftDeleteBaseEntity):
    __tablename__ = "security_group"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    description: Mapped[str | None] = mapped_column("description", String(255), nullable=True)
    version: Mapped[int] = mapped_column("version", Integer, nullable=False, default=0)

    _linked_network_interfaces: Mapped[list["NetworkInterfaceSecurityGroup"]] = relationship(
        "NetworkInterfaceSecurityGroup", lazy="select", back_populates="_security_group"
    )

    @async_property
    async def network_interfaces(self) -> list["NetworkInterface"]:
        linked_network_interfaces: list[NetworkInterfaceSecurityGroup] = \
            await self.awaitable_attrs._linked_network_interfaces
        return [await link.network_interface for link in linked_network_interfaces]

    __mapper_args__ = {"version_id_col": version}

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

    def validate_delete_permission(self, project_id):
        if self.project_id != project_id:
            raise SecurityGroupDeletePermissionDeniedException()

    def validate_update_permission(self, project_id: int):
        if self.project_id != project_id:
            raise SecurityGroupUpdatePermissionDeniedException()

    def update_info(self, name: str, description: str):
        self.name = name
        self.description = description


class NetworkInterfaceSecurityGroup(BaseEntity):
    __tablename__ = "network_interface_security_group"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    network_interface_id: Mapped[int] = mapped_column(
        "network_interface_id", BigInteger, ForeignKey("network_interface.id"), nullable=False
    )
    security_group_id: Mapped[int] = mapped_column(
        "security_group_id",
        BigInteger,
        ForeignKey("security_group.id"),
        nullable=False
    )

    _network_interface: Mapped[Server] = relationship(
        "NetworkInterface", lazy="select", back_populates="_linked_security_groups"
    )
    _security_group: Mapped["SecurityGroup"] = relationship("SecurityGroup", lazy="select",
                                                            back_populates="_linked_network_interfaces")

    @async_property
    async def network_interface(self) -> NetworkInterface:
        return await self.awaitable_attrs._network_interface

    @async_property
    async def security_group(self) -> SecurityGroup:
        return await self.awaitable_attrs._security_group
