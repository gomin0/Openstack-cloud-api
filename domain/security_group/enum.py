from enum import Enum


class SecurityGroupRuleDirection(Enum):
    INGRESS = "ingress"
    EGRESS = "egress"
