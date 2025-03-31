from fastapi import APIRouter

from router.auth.request import LoginRequest
from router.auth.response import LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    path="/login", status_code=200,
    responses={
        401: {"description": "인증 정보가 잘못된 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def login(request: LoginRequest) -> LoginResponse:
    raise NotImplementedError()
