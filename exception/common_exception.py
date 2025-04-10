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
            message="다른 사용자가 데이터를 수정하여 요청하신 내용을 처리할 수 없습니다. 잠시 후 다시 시도해주세요."
        )
