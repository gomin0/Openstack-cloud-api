import enum


class Status(str, enum.Enum):
    ACTIVE = "active"
    MARK_DELETED = "mark_deleted"
    DELETED = "deleted"
