from fastapi import APIRouter, Query, Depends

from api_server.router.user.request import CreateUserRequest, UpdateUserInfoRequest
from common.application.user.response import UserDetailsResponse, UserResponse, UserDetailResponse
from common.application.user.service import UserService
from common.domain.enum import SortOrder
from common.domain.user.enum import UserSortOption
from common.util.auth_token_manager import get_current_user
from common.util.compensating_transaction import compensating_transaction
from common.util.context import CurrentUser

router = APIRouter(prefix="/users", tags=["user"])


@router.get(
    path="", status_code=200,
    summary="유저 목록 조회"
)
async def find_users(
    user_id: int | None = Query(None),
    account_id: str | None = Query(None),
    name: str | None = Query(None),
    sort_by: UserSortOption = Query(UserSortOption.CREATED_AT),
    sort_order: SortOrder = Query(SortOrder.ASC),
    user_service: UserService = Depends()
) -> UserDetailsResponse:
    users: list[UserDetailResponse] = await user_service.find_user_details(
        user_id=user_id,
        account_id=account_id,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        with_relations=True
    )
    return UserDetailsResponse(users=users)


@router.get(
    path="/{user_id}", status_code=200,
    summary="유저 단건 조회",
    responses={
        404: {"description": "user_id에 해당하는 유저를 찾을 수 없는 경우"}
    }
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends()
) -> UserDetailResponse:
    return await user_service.get_user_detail(
        user_id=user_id,
        with_relations=True
    )


@router.post(
    path="", status_code=201,
    summary="유저 생성",
    responses={
        409: {"description": "로그인 id, 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(),
) -> UserResponse:
    async with compensating_transaction() as compensating_tx:
        return await user_service.create_user(
            compensating_tx=compensating_tx,
            account_id=request.account_id,
            name=request.name,
            password=request.password,
        )


@router.put(
    path="/{user_id}/info",
    status_code=200,
    summary="유저 정보 변경",
    responses={422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}}
)
async def update_user_info(
    user_id: int,
    request: UpdateUserInfoRequest,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(),
) -> UserResponse:
    return await user_service.update_user_info(
        request_user_id=current_user.user_id,
        user_id=user_id,
        name=request.name,
    )


@router.delete(
    path="/{user_id}",
    status_code=204,
    summary="유저 삭제",
    responses={
        404: {"description": "<code>user_id</code>에 해당하는 유저가 없는 경우"},
        409: {"description": "마지막 남은 계정을 삭제하려고 하는 경우"},
    }
)
async def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(),
) -> None:
    await user_service.delete_user(
        current_user_id=current_user.user_id,
        user_id=user_id,
    )
