from common.exception.base_exception import CustomException


class OpenStackException(CustomException):
    def __init__(
        self,
        openstack_status_code: int,
        code: str = "OPEN_STACK",
        status_code: int = 500,
        message: str = "OpenStack에서 정의되지 않은 에러가 발생하였습니다.",
    ):
        super().__init__(
            code=code,
            status_code=status_code,
            message=message
        )
        self.openstack_status_code = openstack_status_code
