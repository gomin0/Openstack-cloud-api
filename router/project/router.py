from fastapi import APIRouter, Query, Path, Depends, Body
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.project_service import ProjectService
from common.auth_token_manager import get_current_user
from common.compensating_transaction import compensating_transaction
from common.context import CurrentUser
from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from infrastructure.async_client import get_async_client
from infrastructure.database import get_db_session
from router.project.request import ProjectUpdateRequest
from router.project.response import ProjectListResponse, ProjectResponse, ProjectDetailResponse

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
    project_service: ProjectService = Depends(),
    session: AsyncSession = Depends(get_db_session)
) -> ProjectListResponse:
    projects: list[Project] = await project_service.find_projects(
        session=session,
        ids=ids,
        name=name,
        name_like=name_like,
        sort_by=sort_by,
        order=order,
        with_relations=True
    )
    return ProjectListResponse(
        projects=[await ProjectDetailResponse.from_entity(project) for project in projects]
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
    session: AsyncSession = Depends(get_db_session),
) -> ProjectDetailResponse:
    project: Project = await project_service.get_project(
        session=session,
        project_id=project_id,
        with_relations=True
    )
    return await ProjectDetailResponse.from_entity(project)


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
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client)
) -> ProjectResponse:
    async with compensating_transaction() as compensating_tx:
        project: Project = await project_service.update_project(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
            keystone_token=current_user.keystone_token,
            user_id=current_user.user_id,
            project_id=project_id,
            new_name=request.name
        )
    return ProjectResponse.from_entity(project)


@router.post(
    "/{project_id}/users/{user_id}",
    summary="프로젝트에 계정 소속", status_code=204,
    responses={
        404: {"description": "프로젝트, 계정이 없는 경우"},
        409: {"description": "이미 소속된 경우"}
    }
)
async def assign_role_from_user_on_project(
    project_id: int = Path(description="프로젝트 ID"),
    user_id: int = Path(description="계정 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    project_service: ProjectService = Depends(),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client)
) -> None:
    async with compensating_transaction() as compensating_tx:
        await project_service.assign_role_from_user_on_project(
            compensating_tx=compensating_tx,
            session=session,
            keystone_token=current_user.keystone_token,
            keystone_user_id=current_user.user_id,
            client=client,
            project_id=project_id,
            user_id=user_id,
        )


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
