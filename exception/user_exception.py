from exception.base_exception import CustomException


class UserNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="USER_NOT_FOUND",
            status_code=404,
            message="유저를 찾을 수 없습니다."
        )