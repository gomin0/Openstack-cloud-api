from exception.base_exception import CustomException


class ProjectNotFoundException(CustomException):
    def __init__(self):
        super().__init__(
            code="PROJECT_NOT_FOUND",
            status_code=404,
            message="프로젝트를 찾을 수 없습니다."
        )


class ProjectAccessDeniedException(CustomException):
    def __init__(self, project_id: int | None = None):
        if project_id is None:
            message: str = "해당 프로젝트에 접근할 수 있는 권한이 없습니다."
        else:
            message: str = f"해당 프로젝트에 접근할 수 있는 권한이 없습니다. project_id={project_id}"
        super().__init__(
            code="PROJECT_ACCESS_DENIED",
            status_code=403,
            message=message
        )


class ProjectNameDuplicatedException(CustomException):
    def __init__(self):
        super().__init__(
            code="PROJECT_NAME_DUPLICATED",
            status_code=409,
            message="이미 존재하는 프로젝트 이름입니다."
        )
