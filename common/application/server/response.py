from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from common.domain.floating_ip.entity import FloatingIp
from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.entity import SecurityGroup
from common.domain.server.entity import Server
from common.domain.server.enum import ServerStatus
from common.domain.volume.entity import Volume


class FloatingIpResponse(BaseModel):
    id: int = Field(description="Floating IP id")
    address: str = Field(description="Floating IP address")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, floating_ip: FloatingIp) -> "FloatingIpResponse":
        return cls.model_validate(floating_ip)


class VolumeResponse(BaseModel):
    id: int = Field(description="Volume ID")
    name: str = Field(description="Volume name")
    volume_type_openstack_id: str = Field(description="Volume type (OpenStack ID)")
    size: int = Field(description="Volume size")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, volume: Volume) -> "VolumeResponse":
        return cls.model_validate(volume)


class SecurityGroupResponse(BaseModel):
    id: int = Field(description="Security group ID")
    name: str = Field(description="Security group name")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, security_group: SecurityGroup) -> "SecurityGroupResponse":
        return cls.model_validate(security_group)


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

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, server: Server) -> "ServerResponse":
        return cls.model_validate(server)


class ServerDetailResponse(BaseModel):
    id: int = Field(description="server id")
    name: str = Field(description="Server name")
    description: str | None = Field(default=None, description="Server description")
    project_id: int = Field(description="project id")
    flavor_openstack_id: str = Field(description="flavor openstack id")
    image_openstack_id: str = Field(description="Image OpenStack ID")
    status: ServerStatus = Field(description="Server status")
    fixed_ip_address: list[str] = Field(description="Fixed IP address")
    floating_ip: FloatingIpResponse | None = Field(description="Floating IP info")
    volumes: list[VolumeResponse] = Field(description="List of connected volumes")
    security_groups: list[SecurityGroupResponse] | None = Field(description="List of security groups")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    deleted_at: datetime | None = Field(default=None, description="Deleted at")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_entity(cls, server: Server) -> "ServerDetailResponse":
        volumes: list[Volume] = await server.volumes
        floating_ip: FloatingIp | None = await server.floating_ip
        security_groups: list[SecurityGroup] | None = await server.security_groups
        network_interfaces: list[NetworkInterface] = await server.network_interfaces
        root_volume = next(volume for volume in volumes if volume.is_root_volume)
        return cls(
            id=server.id,
            name=server.name,
            description=server.description,
            project_id=server.project_id,
            flavor_openstack_id=server.flavor_openstack_id,
            image_openstack_id=root_volume.image_openstack_id,
            status=server.status,
            fixed_ip_address=[network_interface.fixed_ip_address for network_interface in network_interfaces],
            floating_ip=FloatingIpResponse.from_entity(floating_ip) if floating_ip else None,
            volumes=[VolumeResponse.from_entity(volume) for volume in volumes],
            security_groups=[
                SecurityGroupResponse.from_entity(security_group) for security_group in security_groups
            ] if security_groups else None,
            created_at=server.created_at,
            updated_at=server.updated_at,
            deleted_at=server.deleted_at,
        )


class ServerDetailsResponse(BaseModel):
    servers: list[ServerDetailResponse]


class ServerVncUrlResponse(BaseModel):
    url: str = Field(description="Server VNC URL")
