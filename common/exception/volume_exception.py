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
