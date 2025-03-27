from fastapi import APIRouter

from router.user.response import UserListResponse, UserResponse

router = APIRouter(prefix="/users", tags=["user"])


@router.get(path="", status_code=200)
def find_users() -> UserListResponse:
    raise NotImplementedError()


@router.get(
    path="/{user_id}", status_code=200,
    responses={
        404: {"description": "user_id에 해당하는 유저를 찾을 수 없는 경우"}
    }
)
def get_user(user_id: int) -> UserResponse:
    raise NotImplementedError()
