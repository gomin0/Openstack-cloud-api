from common.domain.volume.enum import VolumeStatus
from common.exception.base_exception import CustomException


class VolumeNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_NOT_FOUND",
            status_code=404,
            message="볼륨을 찾을 수 없습니다."
        )


class VolumeNameDuplicateException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_NAME_DUPLICATE",
            status_code=409,
            message="이미 사용중인 볼륨 이름입니다."
        )


class VolumeAccessPermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_ACCESS_PERMISSION_DENIED",
            status_code=403,
            message="볼륨에 접근할 수 있는 권한이 없습니다."
        )


class VolumeUpdatePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_UPDATE_PERMISSION_DENIED",
            status_code=403,
            message="볼륨을 수정할 수 있는 권한이 없습니다."
        )


class VolumeDeletePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_DELETE_PERMISSION_DENIED",
            status_code=403,
            message="볼륨을 삭제할 수 있는 권한이 없습니다."
        )


class AttachedVolumeDeletionException(CustomException):
    def __init__(self):
        super().__init__(
            code="ATTACHED_VOLUME_DELETION",
            status_code=409,
            message="서버에 연결된 볼륨은 삭제할 수 없습니다.",
        )


class VolumeStatusInvalidForDeletionException(CustomException):
    def __init__(self, status: VolumeStatus):
        super().__init__(
            code="VOLUME_STATUS_INVALID_FOR_DELETION",
            status_code=409,
            message=f"현재 볼륨 상태({status.value})에서는 삭제할 수 없습니다.",
        )


class VolumeAlreadyDeletedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_ALREADY_DELETED",
            status_code=409,
            message="이미 삭제된 볼륨입니다.",
        )


class VolumeDeletionFailedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_DELETION_FAILED",
            status_code=500,
            message="볼륨 삭제 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


class VolumeStatusInvalidForResizingException(CustomException):
    def __init__(self, status: VolumeStatus):
        super().__init__(
            code="VOLUME_STATUS_INVALID_FOR_RESIZING",
            status_code=409,
            message=f"볼륨 용량을 변경할 수 없습니다. 상태가 AVAILABLE인 볼륨만 용량 변경이 가능합니다. 현재 상태={status.value}"
        )


class VolumeResizeNotAllowedException(CustomException):
    def __init__(self, size: int):
        super().__init__(
            code="VOLUME_RESIZE_NOT_ALLOWED",
            status_code=400,
            message=f"볼륨 용량을 변경할 수 없습니다. 볼륨 용량은 상향 조정만 가능합니다. 유효한 용량으로 변경하고 있는지 확인해주세요. size={size}",
        )


class VolumeResizingFailedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_RESIZING_FAILED",
            status_code=500,
            message=f"알 수 없는 문제로 볼륨 용량 변경에 실패했습니다. 잠시 후 다시 시도해주세요."
        )


class ServerNotMatchedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_NOT_MATCHED",
            status_code=400,
            message="볼륨이 해당 서버에 연결되어 있지 않습니다."
        )
