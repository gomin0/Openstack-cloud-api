from datetime import datetime, timezone

from async_property import async_property
from sqlalchemy import BigInteger, CHAR, ForeignKey, String, Integer, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.project.entity import Project
from common.domain.server.entity import Server
from common.domain.volume.enum import VolumeStatus
from common.exception.volume_exception import (
    AttachedVolumeDeletionException, VolumeStatusInvalidForDeletionException, VolumeAlreadyDeletedException,
    VolumeDeletePermissionDeniedException, VolumeUpdatePermissionDeniedException, VolumeResizeNotAllowedException,
    VolumeStatusInvalidForResizingException, VolumeAccessPermissionDeniedException, VolumeAlreadyAttachedException
)


class Volume(SoftDeleteBaseEntity):
    DELETABLE_STATUSES: list[VolumeStatus] = [
        VolumeStatus.AVAILABLE,
        VolumeStatus.ERROR,
        VolumeStatus.ERROR_RESTORING,
        VolumeStatus.ERROR_EXTENDING,
    ]

    __tablename__ = "volume"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    server_id: Mapped[int | None] = mapped_column("server_id", BigInteger, ForeignKey("server.id"), nullable=True)
    volume_type_openstack_id: Mapped[str] = mapped_column("volume_type_openstack_id", CHAR(36), nullable=False)
    image_openstack_id: Mapped[str | None] = mapped_column("image_openstack_id", CHAR(36), nullable=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    description: Mapped[str] = mapped_column("description", String(255), nullable=False)
    status: Mapped[VolumeStatus] = mapped_column(
        Enum(VolumeStatus, name="status", native_enum=False, length=30),
        nullable=False
    )
    size: Mapped[int] = mapped_column("size", Integer, nullable=False)
    is_root_volume: Mapped[bool] = mapped_column("is_root_volume", Boolean, nullable=False)

    _project: Mapped[Project] = relationship("Project", lazy="select")
    _server: Mapped[Server | None] = relationship("Server", lazy="select", back_populates="_linked_volumes")

    @async_property
    async def project(self) -> Project:
        return await self.awaitable_attrs._project

    @async_property
    async def server(self) -> Server | None:
        return await self.awaitable_attrs._server

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @classmethod
    def create(
        cls,
        openstack_id: str,
        project_id: int,
        volume_type_openstack_id: str,
        image_openstack_id: str | None,
        name: str,
        description: str,
        status: VolumeStatus,
        size: int,
        is_root_volume: bool,
        server_id: int | None = None,
    ) -> "Volume":
        return cls(
            id=None,
            openstack_id=openstack_id,
            project_id=project_id,
            server_id=server_id,
            volume_type_openstack_id=volume_type_openstack_id,
            image_openstack_id=image_openstack_id,
            name=name,
            description=description,
            status=status,
            size=size,
            is_root_volume=is_root_volume,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )

    def validate_owned_by(self, project_id):
        if self.project_id != project_id:
            raise VolumeAccessPermissionDeniedException()

    def validate_update_permission(self, project_id):
        if self.project_id != project_id:
            raise VolumeUpdatePermissionDeniedException()

    def validate_delete_permission(self, project_id):
        if self.project_id != project_id:
            raise VolumeDeletePermissionDeniedException()

    def validate_deletable(self):
        if self.server_id is not None:
            raise AttachedVolumeDeletionException()
        if self.status not in self.DELETABLE_STATUSES:
            raise VolumeStatusInvalidForDeletionException(self.status)
        if self.is_deleted:
            raise VolumeAlreadyDeletedException()

    def validate_resizable(self, size: int):
        if self.status != VolumeStatus.AVAILABLE:
            raise VolumeStatusInvalidForResizingException(self.status)
        if size <= self.size:
            raise VolumeResizeNotAllowedException(size=size)

    def validate_not_attached(self):
        if self.status == VolumeStatus.IN_USE or self._server is not None:
            raise VolumeAlreadyAttachedException(volume_id=self.id)

    def update_info(self, name: str, description: str):
        self.name = name
        self.description = description

    def update_status(self, status: VolumeStatus):
        self.status = status

    def resize(self, size: int):
        self.validate_resizable(size=size)
        self.size = size

    def complete_creation(self, attached: bool):
        if attached:
            self.status = VolumeStatus.IN_USE
        else:
            self.status = VolumeStatus.AVAILABLE

    def prepare_for_attachment(self):
        self.validate_not_attached()
        self.status = VolumeStatus.ATTACHING

    def fail_creation(self) -> None:
        self.status = VolumeStatus.ERROR

    def fail_attachment(self):
        self.status = VolumeStatus.ERROR

    def attach_to_server(self, server):
        self.validate_not_attached()
        self.status = VolumeStatus.IN_USE
        self._server = server

    def detach_from_server(self):
        self._server = None
        self.server_id = None
        self.status = VolumeStatus.AVAILABLE
