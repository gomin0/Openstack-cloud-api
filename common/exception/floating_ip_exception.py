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


class FloatingIpDeletePermissionDeniedException(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_IP_DELETE_PERMISSION_DENIED",
            status_code=403,
            message="floating ip를 삭제할 수 있는 권한이 없습니다."
        )


class AttachedFloatingIpDeletionException(CustomException):
    def __init__(self):
        super().__init__(
            code="ATTACHED_FLOATING_IP_DELETION",
            status_code=409,
            message="서버에 연결된 floating ip는 삭제할 수 없습니다."
        )


class FloatingIpAlreadyDeletedException(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_IP_ALREADY_DELETED",
            status_code=409,
            message="이미 삭제된 floating ip 입니다."
        )


class FloatingIpAlreadyAttachedToNetworkInterfaceException(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_IP_ALREADY_ATTACHED_TO_NETWORK_INTERFACE",
            status_code=409,
            message="해당 floating ip는 이미 network interface 에 할당되어 있습니다."
        )


class FloatingIpNotAttachedToNetworkInterfaceException(CustomException):
    def __init__(self):
        super().__init__(
            code="FLOATING_IP_NOT_ATTACHED_TO_NETWORK_INTERFACE",
            status_code=409,
            message="해당 floating ip는 network interface 에 할당되어 있지 않습니다."
        )
