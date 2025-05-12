from enum import Enum


class SecurityGroupRuleDirection(Enum):
    INGRESS = "ingress"
    EGRESS = "egress"


class SecurityGroupSortOption(Enum):
    NAME = "name"
    CREATED_AT = "created_at"


class SecurityGroupRuleEtherType(Enum):
    IPv4 = "IPv4"
    IPv6 = "IPv6"
