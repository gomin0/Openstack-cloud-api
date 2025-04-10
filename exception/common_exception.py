from exception.base_exception import CustomException


class MultipleEntitiesFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="MULTIPLE_ENTITIES_FOUND",
            status_code=500,
            message="Multiple entities were found when only one was expected."
        )


class OptimisticLockConflictException(CustomException):
    def __init__(self):
        super().__init__(
            code="OPTIMISTIC_LOCK_CONFLICT",
            status_code=409,
            message="작업 중 충돌이 발생했습니다."
        )
