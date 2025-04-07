from exception.base_exception import CustomException


class InvalidAuthException(CustomException):
    def __init__(self):
        super().__init__(
            code="INVALID_AUTH",
            status_code=401,
            message="잘못된 인증 정보입니다. 아이디와 비밀번호를 다시 확인해주세요."
        )


class InvalidAccessTokenException(CustomException):
    def __init__(self):
        super().__init__(
            code="INVALID_ACCESS_TOKEN",
            status_code=401,
            message="유효하지 않은 access token입니다."
        )
