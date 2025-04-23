from dataclasses import dataclass

from domain.security_group.enum import SecurityGroupRuleDirection


@dataclass
class SecurityGroupRuleDTO:
    protocol: str | None
    direction: SecurityGroupRuleDirection
    port_range_min: int
    port_range_max: int
    remote_ip_prefix: str
