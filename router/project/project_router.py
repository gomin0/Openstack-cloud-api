from fastapi import APIRouter

from router.project.response import ProjectListResponse, ProjectResponse

router = APIRouter(prefix="/project", tags=["project"])


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="프로젝트 목록 조회",
    responses={422: {"description": "쿼리 파라미터 오류"}}
)
async def get_projects() -> ProjectListResponse:
    raise NotImplementedError()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="프로젝트 단일 조회",
    responses={
        404: {"description": "해당 ID의 프로젝트를 찾을 수 없는 경우"},
    }
)
async def get_project() -> ProjectResponse:
    raise NotImplementedError()
