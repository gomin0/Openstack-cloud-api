from typing import Literal

from fastapi import APIRouter, Query, Path

from router.project.request import ProjectUpdateRequest
from router.project.response import ProjectListResponse, ProjectResponse

router = APIRouter(prefix="/project", tags=["project"])


@router.get(
    "", status_code=200,
    summary="프로젝트 목록 조회",
    responses={
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"}
    }
)
async def get_projects(
    ids: list[int] = Query(default=None, description="ID 검색"),
    name: str | None = Query(default=None),
    name_like: str | None = Query(default=None),
    sort_by: Literal["name", "created_at"] = Query(default="created_at"),
    order: Literal["asc", "desc"] = Query(default="asc")
) -> ProjectListResponse:
    raise NotImplementedError()


@router.get(
    "/{project_id}", status_code=200,
    summary="프로젝트 단일 조회",
    responses={
        404: {"description": "해당 ID의 프로젝트를 찾을 수 없는 경우"}
    }
)
async def get_project(
    project_id: int = Path(description="프로젝트 ID")
) -> ProjectResponse:
    raise NotImplementedError()


@router.put(
    "/{project_id}",
    summary="프로젝트 변경", status_code=200,
    responses={
        409: {"description": "이름이 중복된 경우"},
        404: {"description": "해당 ID의 프로젝트가 없는 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def update_project(
    request: ProjectUpdateRequest,
    project_id: int = Path(description="프로젝트 ID")
) -> ProjectResponse:
    raise NotImplementedError()


@router.post(
    "/{project_id}/users/{user_id}",
    summary="프로젝트에 계정 소속", status_code=204,
    responses={
        404: {"description": "프로젝트, 계정이 없는 경우"},
        409: {"description": "이미 소속된 경우"}
    }
)
async def assign_account_to_project(
    project_id: int = Path(description="프로젝트 ID"),
    user_id: int = Path(description="계정 ID")
) -> None:
    raise NotImplementedError()


@router.delete(
    "/{project_id}/users/{user_id}",
    summary="프로젝트에서 계정 제외", status_code=204,
    responses={
        404: {"description": "프로젝트, 계정이 없는 경우"},
        409: {"description": "해당 계정이 이 프로젝트에 소속되어 있지 않은 경우"}
    }
)
async def remove_account_from_project(
    project_id: int = Path(description="프로젝트 ID"),
    user_id: int = Path(description="계정 ID")
) -> None:
    raise NotImplementedError()
