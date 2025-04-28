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
    def __init__(self, status):
        super().__init__(
            code="VOLUME_STATUS_INVALID_FOR_DELETION",
            status_code=409,
            message=f"현재 볼륨 상태({status!r})에서는 삭제할 수 없습니다.",
        )


class VolumeAlreadyDeletedException(CustomException):
    def __init__(self):
        super().__init__(
            code="VOLUME_ALREADY_DELETED",
            status_code=409,
            message="이미 삭제된 볼륨입니다.",
        )
