from common.exception.base_exception import CustomException


class ServerNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_NOT_FOUND",
            status_code=404,
            message="서버를 찾을 수 없습니다."
        )


class ServerAccessPermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_ACCESS_PERMISSION_DENIED",
            status_code=403,
            message="해당 서버에 접근할 수 있는 권한이 없습니다."
        )


class ServerUpdatePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_UPDATE_PERMISSION_DENIED",
            status_code=403,
            message="서버를 수정할 수 있는 권한이 없습니다."
        )


class ServerNameDuplicateException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_NAME_DUPLICATE",
            status_code=409,
            message="이미 사용중인 서버 이름입니다."
        )
