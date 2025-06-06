from fastapi import APIRouter, Depends, Body

from api_server.router.auth.request import LoginRequest
from common.application.auth.response import LoginResponse
from common.application.auth.service import AuthService

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
) -> LoginResponse:
    return await auth_service.login(
        project_id=request.project_id,
        account_id=request.account_id,
        password=request.password,
    )
