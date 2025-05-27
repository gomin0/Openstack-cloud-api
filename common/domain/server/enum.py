from enum import Enum


class ServerStatus(Enum):
    ACTIVE = "ACTIVE"
    BUILD = "BUILD"
    DELETED = "DELETED"
    ERROR = "ERROR"
    HARD_REBOOT = "HARD_REBOOT"
    MIGRATING = "MIGRATING"
    PASSWORD = "PASSWORD"
    PAUSED = "PAUSED"
    REBOOT = "REBOOT"
    REBUILD = "REBUILD"
    RESCUE = "RESCUE"
    RESIZE = "RESIZE"
    REVERT_RESIZE = "REVERT_RESIZE"
    SHELVED = "SHELVED"
    SHELVED_OFFLOADED = "SHELVED_OFFLOADED"
    SHUTOFF = "SHUTOFF"
    SOFT_DELETED = "SOFT_DELETED"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"
    VERIFY_RESIZE = "VERIFY_RESIZE"

    @classmethod
    def parse(cls, status: str) -> "ServerStatus":
        normalized_val = status.replace("-", "_").replace(" ", "_").upper()
        try:
            return cls[normalized_val]
        except KeyError:
            raise ValueError(f"Unknown OpenStack server status: {status} → normalized: {normalized_val}")


class ServerSortOption(Enum):
    NAME = "name"
    CREATED_AT = "created_at"
