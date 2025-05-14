from datetime import timezone, datetime

from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.floating_ip.enum import FloatingIpStatus
from common.domain.network_interface.entity import NetworkInterface
from common.exception.floating_ip_exception import FloatingIpDeletePermissionDeniedException, \
    AttachedFloatingIpDeletionException, FloatingIpAlreadyDeletedException


class FloatingIp(SoftDeleteBaseEntity):
    __tablename__ = "floating_ip"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    network_interface_id: Mapped[int | None] = mapped_column(
        "network_interface_id", BigInteger, ForeignKey("network_interface.id"), nullable=True
    )
    status: Mapped[FloatingIpStatus] = mapped_column(
        Enum(FloatingIpStatus, name="status", native_enum=False, length=30),
        nullable=False
    )
    address: Mapped[str] = mapped_column("address", String(15), nullable=False)

    _network_interface: Mapped[NetworkInterface] = relationship(
        "NetworkInterface", lazy="select", back_populates="_floating_ip"
    )

    @async_property
    async def network_interface(self) -> NetworkInterface | None:
        return await self.awaitable_attrs._network_interface

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @classmethod
    def create(
        cls,
        openstack_id: str,
        project_id: int,
        address: str,
    ) -> "FloatingIp":
        return cls(
            id=None,
            openstack_id=openstack_id,
            project_id=project_id,
            network_interface_id=None,
            status=FloatingIpStatus.DOWN,
            address=address,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )

    def validate_delete_permission(self, project_id=project_id):
        if self.project_id != project_id:
            raise FloatingIpDeletePermissionDeniedException()

    def validate_deletable(self):
        if self.network_interface_id is not None:
            raise AttachedFloatingIpDeletionException()
        if self.is_deleted:
            raise FloatingIpAlreadyDeletedException()

    def down_floating_ip(self):
        self.status = FloatingIpStatus.DOWN
