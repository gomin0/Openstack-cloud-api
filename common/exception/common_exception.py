from common.exception.base_exception import CustomException


class MultipleEntitiesFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="MULTIPLE_ENTITIES_FOUND",
            status_code=500,
            message="Multiple entities were found when only one was expected."
        )
