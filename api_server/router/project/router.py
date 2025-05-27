from fastapi import APIRouter, Query, Path, Depends, Body

from api_server.router.project.request import ProjectUpdateRequest
from common.application.project.response import ProjectDetailsResponse, ProjectResponse, ProjectDetailResponse
from common.application.project.service import ProjectService
from common.domain.enum import SortOrder
from common.domain.project.enum import ProjectSortOption
from common.util.auth_token_manager import get_current_user
from common.util.compensating_transaction import compensating_transaction
from common.util.context import CurrentUser

router = APIRouter(prefix="/projects", tags=["project"])


@router.get(
    "", status_code=200,
    summary="프로젝트 목록 조회",
    responses={
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"}
    }
)
async def find_projects(
    ids: list[int] | None = Query(default=None, description="ID 검색"),
    name: str | None = Query(default=None),
    name_like: str | None = Query(default=None),
    sort_by: ProjectSortOption = Query(default=ProjectSortOption.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.ASC),
    project_service: ProjectService = Depends()
) -> ProjectDetailsResponse:
    return await project_service.find_projects_details(
        ids=ids,
        name=name,
        name_like=name_like,
        sort_by=sort_by,
        order=order,
        with_relations=True
    )


@router.get(
    "/{project_id}", status_code=200,
    summary="프로젝트 단일 조회",
    responses={
        404: {"description": "해당 ID의 프로젝트를 찾을 수 없는 경우"}
    }
)
async def get_project(
    project_id: int = Path(description="프로젝트 ID"),
    project_service: ProjectService = Depends(),
) -> ProjectDetailResponse:
    return await project_service.get_project_detail(
        project_id=project_id,
        with_relations=True
    )


@router.put(
    "/{project_id}",
    summary="프로젝트 변경", status_code=200,
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "해당 프로젝트에 대한 접근 권한이 없는 경우"},
        404: {"description": "해당 ID의 프로젝트가 없는 경우"},
        409: {"description": "이름이 중복된 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def update_project(
    request: ProjectUpdateRequest = Body(),
    project_id: int = Path(description="프로젝트 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    project_service: ProjectService = Depends(),
) -> ProjectResponse:
    async with compensating_transaction() as compensating_tx:
        return await project_service.update_project(
            compensating_tx=compensating_tx,
            user_id=current_user.user_id,
            project_id=project_id,
            new_name=request.name
        )


@router.post(
    "/{project_id}/users/{user_id}",
    summary="프로젝트에 계정 소속", status_code=204,
    responses={
        404: {"description": "프로젝트, 계정이 없는 경우"},
        409: {"description": "이미 소속된 경우"}
    }
)
async def assign_user_on_project(
    project_id: int = Path(description="프로젝트 ID"),
    user_id: int = Path(description="계정 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    project_service: ProjectService = Depends(),
) -> None:
    async with compensating_transaction() as compensating_tx:
        await project_service.assign_user_on_project(
            compensating_tx=compensating_tx,
            request_user_id=current_user.user_id,
            project_id=project_id,
            user_id=user_id,
        )


@router.delete(
    "/{project_id}/users/{user_id}",
    summary="프로젝트에서 계정 제외", status_code=204,
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "해당 프로젝트에 대한 접근 권한이 없는 경우"},
        404: {"description": "프로젝트, 계정이 없는 경우"},
        409: {"description": "해당 계정이 이 프로젝트에 소속되어 있지 않은 경우"}
    }
)
async def unassign_user_from_project(
    project_id: int = Path(description="프로젝트 ID"),
    user_id: int = Path(description="계정 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    project_service: ProjectService = Depends(),
) -> None:
    async with compensating_transaction() as compensating_tx:
        await project_service.unassign_user_from_project(
            compensating_tx=compensating_tx,
            request_user_id=current_user.user_id,
            project_id=project_id,
            user_id=user_id,
        )
