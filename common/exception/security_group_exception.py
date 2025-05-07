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
            message="해당 보안 그룹에 접근할 수 있는 권한이 없습니다."
        )


class SecurityGroupDeletePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SECURITY_GROUP_DELETE_PERMISSION_DENIED_EXCEPTION",
            status_code=403,
            message="해당 보안 그룹을 삭제할 수 있는 권한이 없습니다."
        )


class AttachedSecurityGroupDeletionException(CustomException):
    def __init__(self):
        super().__init__(
            code="ATTACHED_SECURITY_GROUP_DELETION",
            status_code=409,
            message="서버에 연결된 보안 그룹은 삭제할 수 없습니다."
        )


class SecurityGroupNameDuplicatedException(CustomException):
    def __init__(self):
        super().__init__(
            code="SECURITY_GROUP_NAME_DUPLICATED",
            status_code=409,
            message="이미 프로젝트 내에 존재하는 보안 그룹 이름입니다."
        )
