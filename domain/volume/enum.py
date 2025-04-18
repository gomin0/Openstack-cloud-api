from enum import Enum


class VolumeStatus(Enum):
    CREATING = "creating"
    AVAILABLE = "available"
    RESERVED = "reserved"
    ATTACHING = "attaching"
    DETACHING = "detaching"
    IN_USE = "in-use"
    MAINTENANCE = "maintenance"
    DELETING = "deleting"
    AWAITING_TRANSFER = "awaiting-transfer"
    ERROR = "error"
    ERROR_DELETING = "error_deleting"
    BACKING_UP = "backing-up"
    RESTORING_BACKUP = "restoring-backup"
    ERROR_BACKING_UP = "error_backing-up"
    ERROR_RESTORING = "error_restoring"
    ERROR_EXTENDING = "error_extending"
    DOWNLOADING = "downloading"
    UPLOADING = "uploading"
    RETYPING = "retyping"
    EXTENDING = "extending"
