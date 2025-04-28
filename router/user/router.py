from fastapi import APIRouter, Query, Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.user.response import UserDetailsResponse, UserResponse, UserDetailResponse
from application.user.service import UserService
from domain.enum import SortOrder
from domain.user.enum import UserSortOption
from infrastructure.async_client import get_async_client
from infrastructure.database import get_db_session
from router.user.request import CreateUserRequest, UpdateUserInfoRequest
from util.auth_token_manager import get_current_user
from util.compensating_transaction import compensating_transaction
from util.context import CurrentUser

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
    user_service: UserService = Depends(),
    session: AsyncSession = Depends(get_db_session)
) -> UserDetailsResponse:
    users: list[UserDetailResponse] = await user_service.find_user_details(
        session=session,
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
    user_service: UserService = Depends(),
    session: AsyncSession = Depends(get_db_session)
) -> UserDetailResponse:
    return await user_service.get_user_detail(
        session=session,
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
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
) -> UserResponse:
    async with compensating_transaction() as compensating_tx:
        return await user_service.create_user(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
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
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await user_service.update_user_info(
        session=session,
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
def delete_user(user_id: int) -> None:
    raise NotImplementedError()
