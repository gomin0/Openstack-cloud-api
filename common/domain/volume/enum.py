from enum import Enum


class VolumeStatus(Enum):
    CREATING = "CREATING"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    ATTACHING = "ATTACHING"
    DETACHING = "DETACHING"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"
    DELETING = "DELETING"
    AWAITING_TRANSFER = "AWAITING_TRANSFER"
    ERROR = "ERROR"
    ERROR_DELETING = "ERROR_DELETING"
    BACKING_UP = "BACKING_UP"
    RESTORING_BACKUP = "RESTORING_BACKUP"
    ERROR_BACKING_UP = "ERROR_BACKING_UP"
    ERROR_RESTORING = "ERROR_RESTORING"
    ERROR_EXTENDING = "ERROR_EXTENDING"
    DOWNLOADING = "DOWNLOADING"
    UPLOADING = "UPLOADING"
    RETYPING = "RETYPING"
    EXTENDING = "EXTENDING"

    @classmethod
    def parse(cls, status: str) -> "VolumeStatus":
        normalized_val = status.replace("-", "_").replace(" ", "_").upper()
        try:
            return cls[normalized_val]
        except KeyError:
            raise ValueError(f"Unknown OpenStack volume status: {status} → normalized: {normalized_val}")


class VolumeSortOption(Enum):
    CREATED_AT = "created_at"
    NAME = "name"
