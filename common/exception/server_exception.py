from common.domain.server.enum import ServerStatus
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


class ServerStatusInvalidToStartException(CustomException):
    def __init__(self, status: ServerStatus):
        super().__init__(
            code="SERVER_STATUS_INVALID_TO_START",
            status_code=409,
            message=f"현재 서버 상태{status.value} 에서는 시작할 수 없습니다."
        )


class ServerStatusInvalidToStopException(CustomException):
    def __init__(self, status: ServerStatus):
        super().__init__(
            code="SERVER_STATUS_INVALID_TO_STOP",
            status_code=409,
            message=f"현재 서버 상태{status.value} 에서는 중지할 수 없습니다."
        )


class UnsupportedServerStatusUpdateRequestException(CustomException):
    def __init__(self):
        super().__init__(
            code="INVALID_SERVER_STATUS_UPDATE_REQUEST",
            status_code=400,
            message="해당 상태로 변경 할 수 없습니다. ACTICE or SHUTOFF 상태만 요청 가능합니다."
        )


class ServerStartFailedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_START_FAILED",
            status_code=500,
            message="서버 시작 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


class ServerStopFailedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SERVER_STOP_FAILED",
            status_code=500,
            message="서버 중지 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
