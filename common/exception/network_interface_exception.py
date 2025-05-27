from common.exception.base_exception import CustomException


class NetworkInterfaceNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="NETWORK_INTERFACE_NOT_FOUND",
            status_code=404,
            message="해당 network interface 를 찾을 수 없습니다."
        )


class NetworkInterfaceAccessPermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="NETWORK_INTERFACE_ACCESS_PERMISSION_DENIED",
            status_code=403,
            message="해당 network interface 에 접근할 수 있는 권한이 없습니다."
        )
