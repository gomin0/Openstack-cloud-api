from exception.base_exception import CustomException


class ProjectNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="PROJECT_NOT_FOUND",
            status_code=404,
            message="프로젝트를 찾을 수 없습니다."
        )
