from common.exception.base_exception import CustomException


class UserNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="USER_NOT_FOUND",
            status_code=404,
            message="유저를 찾을 수 없습니다."
        )


class UserNotJoinedAnyProjectException(CustomException):
    def __init__(self):
        super().__init__(
            code="USER_NOT_JOINED_ANY_PROJECT",
            status_code=400,
            message="유저가 소속된 프로젝트가 존재하지 않습니다."
        )


class UserAccountIdDuplicateException(CustomException):
    def __init__(self, account_id: str):
        super().__init__(
            code="USER_ACCOUNT_ID_DUPLICATE",
            status_code=409,
            message=f"이미 사용중인 계정 ID 입니다. account_id={account_id}"
        )


class UserUpdatePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="USER_UPDATE_PERMISSION_DENIED",
            status_code=403,
            message="유저를 변경할 권한이 없습니다."
        )


class UserDeletePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="USER_DELETE_PERMISSION_DENIED",
            status_code=403,
            message="유저를 삭제할 수 있는 권한이 없습니다."
        )


class LastUserDeletionNotAllowedException(CustomException):
    def __init__(self):
        super().__init__(
            code="LAST_USER_DELETION_NOT_ALLOWED",
            status_code=403,
            message="도메인의 마지막 유저를 삭제할 수 없습니다."
        )
