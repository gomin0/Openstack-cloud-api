from pydantic import BaseModel, Field


class CreateVolumeRequest(BaseModel):
    name: str = Field(max_length=255, description="Name of volume", examples=["volume-001"])
    description: str = Field(max_length=255, description="Description of volume", examples=["For test"])
    size: int = Field(description="용량(GiB)", examples=[1])
    volume_type_id: str = Field(
        min_length=36,
        max_length=36,
        description="사용할 volume type의 uuid",
        examples=["64abcd22-a30b-4982-8f82-332e89ff4bf7"]
    )
    image_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="사용할 부팅 이미지의 uuid",
        examples=["1abc7a2f-8eec-49a2-b9ef-be16e0959cdb"]
    )


class CreateServerRequest(BaseModel):
    name: str = Field(max_length=255, description="Server name")
    description: str | None = Field(max_length=255, default=None, description="Server description")
    flavor_openstack_id: str = Field(description="flavor openstack id")
    network_openstack_id: str = Field(description="network openstack id")
    volume: CreateVolumeRequest = Field(description="root volume info to create")
    security_group_ids: list[int] = Field(description="security group ids")


class UpdateServerInfoRequest(BaseModel):
    name: str = Field(max_length=255, description="Server name")
    description: str | None = Field(max_length=255, default=None, description="Server description")
