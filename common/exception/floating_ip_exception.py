from common.exception.base_exception import CustomException


class FloatingIpNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_IP_NOT_FOUND",
            status_code=404,
            message="floating ip를 찾을 수 없습니다."
        )


class FloatingIpAccessDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_IP_ACCESS_DENIED",
            status_code=403,
            message="해당 floating ip에 접근할 수 있는 권한이 없습니다."
        )
