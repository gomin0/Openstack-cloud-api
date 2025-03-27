from fastapi import APIRouter

from router.project.request import ProjectUpdateRequest
from router.project.response import ProjectListResponse, ProjectResponse, ProjectAccountAssignResponse, \
    ProjectAccountRemoveResponse

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


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="프로젝트 변경",
    responses={
        400: {"description": "이름이 중복된 경우"},
        404: {"description": "해당 ID의 프로젝트가 없는 경우"},
        500: {"description": "OpenStack 연동 실패 등 내부 에러"},
    }
)
async def update_project(request: ProjectUpdateRequest) -> ProjectResponse:
    raise NotImplementedError()


@router.put(
    "/{project_id}/users/{user_id}/roles/{role_id}",
    response_model=ProjectAccountAssignResponse,
    summary="프로젝트에 계정 소속",
    responses={
        404: {"description": "프로젝트, 계정 또는 role이 없는 경우"},
        409: {"description": "이미 소속된 경우"},
        500: {"description": "OpenStack 실패 등으로 롤백된 경우"},
    }
)
async def assign_account_to_project() -> ProjectAccountAssignResponse:
    raise NotImplementedError()


@router.delete(
    "/{project_id}/users/{user_id/roles/{role_id}",
    response_model=ProjectAccountRemoveResponse,
    summary="프로젝트에서 계정 제외",
    responses={
        404: {"description": "프로젝트, 계정 또는 role이 없는 경우"},
        409: {"description": "해당 계정이 이 프로젝트에 소속되어 있지 않은 경우"},
        500: {"description": "OpenStack 연동 실패 등으로 롤백된 경우"}
    }
)
async def remove_account_from_project() -> ProjectAccountRemoveResponse:
    raise NotImplementedError()
