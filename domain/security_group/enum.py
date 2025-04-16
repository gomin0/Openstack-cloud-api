from enum import Enum


class SecurityGroupRuleDirection(Enum):
    INGRESS = "ingress"
    EGRESS = "egress"


class SecurityGroupSortOption(Enum):
    NAME = "name"
    CREATED_AT = "created_at"
