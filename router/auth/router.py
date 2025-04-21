from fastapi import APIRouter, Depends, Body
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.response import LoginResponse
from application.auth.service import AuthService
from infrastructure.async_client import get_async_client
from infrastructure.database import get_db_session
from router.auth.request import LoginRequest

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
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client)
) -> LoginResponse:
    return await auth_service.login(
        session=session,
        client=client,
        project_id=request.project_id,
        account_id=request.account_id,
        password=request.password,
    )
