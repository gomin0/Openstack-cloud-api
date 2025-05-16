from async_property import async_property
from sqlalchemy import CHAR, BigInteger, ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.server.enum import ServerStatus
from common.exception.server_exception import ServerAccessPermissionDeniedException, \
    ServerUpdatePermissionDeniedException, ServerStatusInvalidToStartException, ServerStatusInvalidToStopException


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

    _linked_volumes: Mapped[list["Volume"]] = relationship("Volume", lazy="select")
    _linked_network_interfaces: Mapped[list["NetworkInterface"]] = relationship(
        "NetworkInterface", lazy="select", back_populates="_server"
    )

    @async_property
    async def volumes(self) -> list["Volume"]:
        return await self.awaitable_attrs._linked_volumes

    @async_property
    async def network_interfaces(self) -> list["NetworkInterface"]:
        return await self.awaitable_attrs._linked_network_interfaces

    def validate_access_permission(self, project_id):
        if self.project_id != project_id:
            raise ServerAccessPermissionDeniedException()

    def validate_update_permission(self, project_id):
        if self.project_id != project_id:
            raise ServerUpdatePermissionDeniedException()

    def update_info(self, name: str, description: str):
        self.name = name
        self.description = description

    def validate_startable(self):
        if self.status != ServerStatus.SHUTOFF:
            raise ServerStatusInvalidToStartException(self.status)

    def validate_stoppable(self):
        if self.status != ServerStatus.ACTIVE and self.status != ServerStatus.ERROR:
            raise ServerStatusInvalidToStopException(self.status)

    def start(self):
        self.status = ServerStatus.ACTIVE

    def stop(self):
        self.status = ServerStatus.SHUTOFF
