from common.exception.base_exception import CustomException


class FloatingNetworkNotFound(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_NETWORK_NOT_FOUND",
            status_code=404,
            message="floating ip를 할당 받을 network를 찾을 수 없습니다."
        )
