from fastapi import APIRouter, Depends, Body
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth_service import AuthService
from application.keystone_service import KeystoneService
from application.project_service import ProjectService
from common.auth_token_manager import create_access_token
from domain.keystone.model import KeystoneToken
from domain.project.entity import Project
from domain.user.entitiy import User
from exception.project_exception import ProjectAccessDeniedException
from exception.user_exception import UserNotJoinedAnyProjectException
from infrastructure.async_client import get_async_client
from infrastructure.database import get_db_session
from router.auth.request import LoginRequest
from router.auth.response import LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    path="/login", status_code=200,
    responses={
        400: {"description": "유저가 소속된 프로젝트가 없는 경우."},
        401: {"description": "인증 정보가 잘못된 경우"},
        403: {"description": "<code>project_id</code>에 해당하는 프로젝트에 소속되지 않았거나 접근 권한이 없는 경우."},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def login(
    request: LoginRequest = Body(),
    auth_service: AuthService = Depends(),
    project_service: ProjectService = Depends(),
    keystone_service: KeystoneService = Depends(),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client)
) -> LoginResponse:
    # account_id, password로 유저 인증 및 조회
    user: User = await auth_service.authenticate_user(
        session=session,
        account_id=request.account_id,
        password=request.password,
    )

    # Keystone token 발급을 위한 프로젝트 선택
    joined_projects: list[Project] = await user.projects
    if request.project_id is not None:
        # 요청 받은 프로젝트 조회 및 선택
        project: Project = await project_service.get_project(
            session=session,
            project_id=request.project_id,
            with_relations=True
        )
        if project not in joined_projects:
            raise ProjectAccessDeniedException(project_id=request.project_id)
    else:
        # 소속된 프로젝트 중 하나 선택
        if len(joined_projects) == 0:
            raise UserNotJoinedAnyProjectException()
        project: Project = joined_projects[0]

    # Keystone token 발급
    keystone_token: KeystoneToken = await keystone_service.issue_keystone_token(
        client=client,
        user_openstack_id=user.openstack_id,
        password=request.password,
        project_openstack_id=project.openstack_id,
    )

    # Access token 발급
    access_token: str = create_access_token(
        user_id=user.id,
        keystone_token=keystone_token
    )

    return LoginResponse(
        user=UserResponse.model_validate(user),
        token=access_token,
    )
