from enum import Enum


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class LifecycleStatus(Enum):
    ACTIVE = "ACTIVE"
    MARK_DELETED = "MARK_DELETED"
    DELETED = "DELETED"
