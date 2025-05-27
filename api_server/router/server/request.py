from pydantic import BaseModel, Field

from common.application.server.dto import CreateServerCommand


class CreateRootVolumeRequest(BaseModel):
    size: int = Field(description="용량(GiB)", examples=[1])
    image_id: str = Field(
        min_length=36,
        max_length=36,
        description="사용할 부팅 이미지의 uuid",
        examples=["1abc7a2f-8eec-49a2-b9ef-be16e0959cdb"]
    )


class CreateServerRequest(BaseModel):
    name: str = Field(max_length=255, description="Server name")
    description: str = Field(max_length=255, description="Server description")
    flavor_id: str = Field(description="flavor openstack id")
    network_id: str = Field(description="network openstack id")
    root_volume: CreateRootVolumeRequest = Field(description="root volume info to create")
    security_group_ids: list[int] = Field(description="security group ids")

    def to_command(
        self,
        keystone_token: str,
        current_project_id: int,
        current_project_openstack_id: str,
    ) -> CreateServerCommand:
        return CreateServerCommand(
            keystone_token=keystone_token,
            current_project_id=current_project_id,
            current_project_openstack_id=current_project_openstack_id,
            name=self.name,
            description=self.description,
            flavor_openstack_id=self.flavor_id,
            network_openstack_id=self.network_id,
            root_volume=CreateServerCommand.RootVolume(
                size=self.root_volume.size,
                image_openstack_id=self.root_volume.image_id,
            ),
            security_group_ids=self.security_group_ids,
        )


class UpdateServerInfoRequest(BaseModel):
    name: str = Field(max_length=255, description="Server name")
    description: str | None = Field(max_length=255, default=None, description="Server description")
