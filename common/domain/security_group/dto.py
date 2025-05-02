from datetime import datetime

from pydantic.dataclasses import dataclass

from common.domain.security_group.enum import SecurityGroupRuleDirection


@dataclass
class SecurityGroupRuleDTO:
    openstack_id: str
    security_group_openstack_id: str
    protocol: str | None
    direction: SecurityGroupRuleDirection
    port_range_min: int | None
    port_range_max: int | None
    remote_ip_prefix: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateSecurityGroupRuleDTO:
    protocol: str | None
    direction: SecurityGroupRuleDirection
    port_range_min: int | None
    port_range_max: int | None
    remote_ip_prefix: str | None


@dataclass
class SecurityGroupDTO:
    openstack_id: str
    rules: list[SecurityGroupRuleDTO]
    name: str
    description: str | None
