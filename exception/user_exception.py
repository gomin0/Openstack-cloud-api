from exception.base_exception import CustomException


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


class UserNameDuplicateException(CustomException):
    def __init__(self, name: str):
        super().__init__(
            code="USER_NAME_DUPLICATE",
            status_code=409,
            message=f"이미 사용중인 이름입니다. name={name}"
        )
