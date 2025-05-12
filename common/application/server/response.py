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
    network_interface_id: int | None = Field(description="Network interface id")
    address: str = Field(description="Floating IP address")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, floating_ip: FloatingIp) -> "FloatingIpResponse":
        return cls.model_validate(floating_ip)


class VolumeResponse(BaseModel):
    id: int = Field(description="Volume ID")
    name: str = Field(description="Volume name")
    volume_type_id: str = Field(description="Volume type (OpenStack ID)")
    size: int = Field(description="Volume size")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, volume: Volume) -> "VolumeResponse":
        return cls(
            id=volume.id,
            name=volume.name,
            volume_type_id=volume.volume_type_openstack_id,
            size=volume.size,
        )


class SecurityGroupResponse(BaseModel):
    id: int = Field(description="Security group ID")
    name: str = Field(description="Security group name")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, security_group: SecurityGroup) -> "SecurityGroupResponse":
        return cls.model_validate(security_group)


class ServerResponse(BaseModel):
    id: int = Field(description="server id")
    openstack_id: str = Field(description="OpenStack ID")
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
    flavor_id: str = Field(description="flavor openstack id")
    image_id: str = Field(description="Image OpenStack ID")
    status: ServerStatus = Field(description="Server status")
    fixed_ip_addresses: list[str] = Field(description="Fixed IP address")
    floating_ips: list[FloatingIpResponse] | None = Field(description="Floating IP info")
    volumes: list[VolumeResponse] = Field(description="List of connected volumes")
    security_groups: list[SecurityGroupResponse] | None = Field(description="List of security groups")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    deleted_at: datetime | None = Field(default=None, description="Deleted at")

    @classmethod
    async def from_entity(cls, server: Server) -> "ServerDetailResponse":
        volumes: list[Volume] = await server.volumes
        security_groups: list[SecurityGroup] = await server.security_groups
        network_interfaces: list[NetworkInterface] = await server.network_interfaces
        root_volume: Volume = next(volume for volume in volumes if volume.is_root_volume)
        floating_ips: list[FloatingIp] = []
        for network_interface in network_interfaces:
            floating_ip: FloatingIp | None = await network_interface.floating_ip
            if floating_ip:
                floating_ips.append(floating_ip)

        return cls(
            id=server.id,
            name=server.name,
            description=server.description,
            project_id=server.project_id,
            flavor_id=server.flavor_openstack_id,
            image_id=root_volume.image_openstack_id,
            status=server.status,
            fixed_ip_addresses=[network_interface.fixed_ip_address for network_interface in network_interfaces],
            floating_ips=[FloatingIpResponse.from_entity(floating_ip) for floating_ip in floating_ips],
            volumes=[VolumeResponse.from_entity(volume) for volume in volumes],
            security_groups=[
                SecurityGroupResponse.from_entity(security_group) for security_group in security_groups
            ],
            created_at=server.created_at,
            updated_at=server.updated_at,
            deleted_at=server.deleted_at,
        )


class ServerDetailsResponse(BaseModel):
    servers: list[ServerDetailResponse]


class ServerVncUrlResponse(BaseModel):
    url: str = Field(description="Server VNC URL")
