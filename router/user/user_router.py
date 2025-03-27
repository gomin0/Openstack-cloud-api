from fastapi import APIRouter

from router.user.request import SignUpRequest
from router.user.response import UserListResponse, UserResponse

router = APIRouter(prefix="/users", tags=["user"])


@router.get(
    path="", status_code=200,
    summary="유저 목록 조회"
)
def find_users() -> UserListResponse:
    raise NotImplementedError()


@router.get(
    path="/{user_id}", status_code=200,
    summary="유저 단건 조회",
    responses={
        404: {"description": "user_id에 해당하는 유저를 찾을 수 없는 경우"}
    }
)
def get_user(user_id: int) -> UserResponse:
    raise NotImplementedError()


@router.post(
    path="", status_code=201,
    summary="회원 가입",
    responses={
        409: {"description": "로그인 id, 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
def sign_up(reqeust: SignUpRequest) -> UserResponse:
    raise NotImplementedError()
