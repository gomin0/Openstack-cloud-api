from fastapi import APIRouter, Query

from domain.enum import SortOrder
from domain.user.enum import UserSortOption
from router.user.request import SignUpRequest, CreateUserRequest, UpdateUserRequest
from router.user.response import UserDetailsResponse, UserResponse, UserDetailResponse

router = APIRouter(prefix="/users", tags=["user"])


@router.get(
    path="", status_code=200,
    summary="유저 목록 조회"
)
def find_users(
    user_id: str | None = Query(None),
    account_id: str | None = Query(None),
    name: str | None = Query(None),
    sort_by: UserSortOption = Query(UserSortOption.CREATED_AT),
    sort_order: SortOrder = Query(SortOrder.ASC),
) -> UserDetailsResponse:
    raise NotImplementedError()


@router.get(
    path="/{user_id}", status_code=200,
    summary="유저 단건 조회",
    responses={
        404: {"description": "user_id에 해당하는 유저를 찾을 수 없는 경우"}
    }
)
def get_user(user_id: int) -> UserDetailResponse:
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


@router.post(
    path="", status_code=201,
    summary="유저 생성",
    responses={
        409: {"description": "로그인 id, 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
def create_user(request: CreateUserRequest) -> UserResponse:
    raise NotImplementedError()


@router.patch(
    path="/{user_id}", status_code=200,
    summary="유저 정보 변경",
    responses={
        409: {"description": "변경하려는 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
def update_user(user_id: int, request: UpdateUserRequest) -> UserResponse:
    raise NotImplementedError()


@router.delete(
    path="/{user_id}", status_code=204,
    summary="유저 삭제",
    responses={
        409: {"description": "마지막 남은 계정을 삭제하려고 하는 경우"}
    }
)
def delete_user(user_id: int) -> None:
    raise NotImplementedError()
