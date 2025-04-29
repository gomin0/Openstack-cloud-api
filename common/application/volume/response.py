from datetime import datetime

from pydantic import BaseModel, Field

from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus


class VolumeResponse(BaseModel):
    id: int = Field(description="Id of volume")
    openstack_id: str = Field(description="OpenStack id of volume", examples=["64abcd22-a30b-4982-8f82-332e89ff4bf1"])
    project_id: int = Field(description="Id of project")
    server_id: int | None = Field(default=None, description="Id of server")
    volume_type_id: str = Field(description="Id of volume type", examples=["64abcd22-a30b-4982-8f82-332e89ff4bf1"])
    image_id: str = Field(description="Id of boot image", examples=["2fcc7a2f-8eec-49a2-b9ef-be16e0959cdb"])
    name: str = Field(description="Name of volume", examples=["volume-001"])
    description: str = Field(description="Description of volume", examples=["volume-001"])
    status: VolumeStatus = Field(description="Status of volume")
    size: int = Field(description="Size of volume(GiB)")
    is_root_volume: bool = Field(description="Whether it is a root volume")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    deleted_at: datetime | None = Field(default=None, description="Deletion time")

    @classmethod
    def from_entity(cls, volume: Volume) -> "VolumeResponse":
        return cls(
            id=volume.id,
            openstack_id=volume.openstack_id,
            project_id=volume.project_id,
            server_id=volume.server_id,
            volume_type_id=volume.volume_type_openstack_id,
            image_id=volume.image_openstack_id,
            name=volume.name,
            description=volume.description,
            status=volume.status,
            size=volume.size,
            is_root_volume=volume.is_root_volume,
            created_at=volume.created_at,
            updated_at=volume.updated_at,
            deleted_at=volume.deleted_at,
        )


class ServerResponse(BaseModel):
    id: int = Field(description="Id of server")
    name: str = Field(description="Name of server", examples=["server-001"])
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    deleted_at: datetime | None = Field(default=None, description="Deletion time")


class VolumeDetailResponse(BaseModel):
    id: int = Field(description="Id of volume")
    project_id: int = Field(description="Id of project")
    server: ServerResponse | None = Field(default=None, description="Server information")
    volume_type_id: str = Field(description="Id of volume type", examples=["64abcd22-a30b-4982-8f82-332e89ff4bf1"])
    image_id: str = Field(description="Id of boot image", examples=["2fcc7a2f-8eec-49a2-b9ef-be16e0959cdb"])
    name: str = Field(description="Name of volume", examples=["volume-001"])
    description: str = Field(description="Description of volume", examples=["volume-001"])
    status: VolumeStatus = Field(description="Status of volume")
    size: int = Field(description="Size of volume(GiB)")
    is_root_volume: bool = Field(description="Whether it is a root volume")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    deleted_at: datetime | None = Field(default=None, description="Deletion time")


class VolumesDetailResponse(BaseModel):
    volumes: list[VolumeDetailResponse]
