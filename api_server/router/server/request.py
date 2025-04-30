from pydantic import BaseModel, Field


class CreateRootVolumeRequest(BaseModel):
    volume_size: int = Field(description="size of root volume")
    image_openstack_id: str = Field(description="image openstack id")


class CreateServerRequest(BaseModel):
    name: str = Field(max_length=255, description="Server name")
    description: str | None = Field(max_length=255, default=None, description="Server description")
    flavor_openstack_id: str = Field(description="flavor openstack id")
    network_openstack_id: str = Field(description="network openstack id")
    volume: CreateRootVolumeRequest = Field(description="root volume info to create")
    security_group_ids: list[int] = Field(description="security group ids")


class UpdateServerInfoRequest(BaseModel):
    name: str = Field(max_length=255, description="Server name")
    description: str | None = Field(max_length=255, default=None, description="Server description")
