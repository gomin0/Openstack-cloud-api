from pydantic.dataclasses import dataclass

from common.domain.security_group.enum import SecurityGroupRuleDirection


@dataclass
class SecurityGroupRuleDTO:
    openstack_id: str
    security_group_openstack_id: str
    protocol: str | None
    ether_type: str
    direction: SecurityGroupRuleDirection
    port_range_min: int | None
    port_range_max: int | None
    remote_ip_prefix: str | None

    def to_update_dto(self) -> "UpdateSecurityGroupRuleDTO":
        return UpdateSecurityGroupRuleDTO(
            protocol=self.protocol,
            ether_type=self.ether_type,
            direction=self.direction,
            port_range_min=self.port_range_min,
            port_range_max=self.port_range_max,
            remote_ip_prefix=self.remote_ip_prefix
        )


@dataclass
class CreateSecurityGroupRuleDTO:
    protocol: str | None
    ether_type: str
    direction: SecurityGroupRuleDirection
    port_range_min: int | None
    port_range_max: int | None
    remote_ip_prefix: str | None


@dataclass
class UpdateSecurityGroupRuleDTO:
    protocol: str | None
    ether_type: str
    direction: SecurityGroupRuleDirection
    port_range_min: int | None
    port_range_max: int | None
    remote_ip_prefix: str | None

    def to_create_dto(self) -> "CreateSecurityGroupRuleDTO":
        return CreateSecurityGroupRuleDTO(
            protocol=self.protocol,
            ether_type=self.ether_type,
            direction=self.direction,
            port_range_min=self.port_range_min,
            port_range_max=self.port_range_max,
            remote_ip_prefix=self.remote_ip_prefix,
        )


@dataclass
class SecurityGroupDTO:
    openstack_id: str
    rules: list[SecurityGroupRuleDTO]
    name: str
    description: str | None
