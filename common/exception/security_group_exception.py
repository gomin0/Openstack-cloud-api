from common.exception.base_exception import CustomException


class SecurityGroupNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="SECURITY_GROUP_NOT_FOUND",
            status_code=404,
            message="보안 그룹을 찾을 수 없습니다."
        )


class SecurityGroupAccessDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SECURITY_GROUP_ACCESS_DENIED",
            status_code=403,
            message="해당 보안 그룹에 접근할 수 권한이 없습니다."
        )
