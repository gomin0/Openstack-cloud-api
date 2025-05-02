from datetime import datetime

from pydantic import BaseModel, Field

from common.domain.server.enum import ServerStatus


class FloatingIpResponse(BaseModel):
    id: int = Field(description="Floating IP id")
    address: str = Field(description="Floating IP address")


class VolumeResponse(BaseModel):
    id: int = Field(description="Volume ID")
    name: str = Field(description="Volume name")
    volume_type_id: str = Field(description="Volume type (OpenStack ID)")
    size: int = Field(description="Volume size")


class SecurityGroupResponse(BaseModel):
    id: int = Field(description="Security group ID")
    name: str = Field(description="Security group name")


class ServerResponse(BaseModel):
    id: int = Field(description="server id")
    project_id: int = Field(description="project id")
    flavor_openstack_id: str = Field(description="flavor openstack id")
    name: str = Field(description="server name")
    description: str | None = Field(default=None, description="server description")
    status: ServerStatus = Field(description="server status")
    created_at: datetime = Field(description="server created at")
    updated_at: datetime = Field(description="server updated at")
    deleted_at: datetime | None = Field(description="server deleted at")


class ServerDetailResponse(BaseModel):
    id: int = Field(description="server id")
    name: str = Field(description="Server name")
    description: str | None = Field(default=None, description="Server description")
    project_id: int = Field(description="project id")
    flavor_openstack_id: str = Field(description="flavor openstack id")
    image_id: str = Field(description="Image OpenStack ID")
    image_name: str = Field(description="Image name")
    status: ServerStatus = Field(description="Server status")
    fixed_ip_address: str = Field(description="Fixed IP address")
    floating_ip: FloatingIpResponse | None = Field(description="Floating IP info")
    volumes: list[VolumeResponse] | None = Field(description="List of connected volumes")
    security_groups: list[SecurityGroupResponse] | None = Field(description="List of security groups")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    deleted_at: datetime | None = Field(default=None, description="Deleted at")


class ServerDetailsResponse(BaseModel):
    servers: list[ServerDetailResponse]


class ServerVncUrlResponse(BaseModel):
    url: str = Field(description="Server VNC URL")
