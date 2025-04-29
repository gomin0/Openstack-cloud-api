from enum import Enum


class FloatingIpStatus(Enum):
    ACTIVE = "ACTIVE"
    DOWN = "DOWN"
    ERROR = "ERROR"


class FloatingIpSortOption(Enum):
    ADDRESS = "address"
    CREATED_AT = "created_at"
