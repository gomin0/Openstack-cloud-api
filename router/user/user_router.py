from fastapi import APIRouter

from router.user.response import UserListResponse

router = APIRouter(prefix="/users", tags=["user"])


@router.get("", status_code=200)
def find_users() -> UserListResponse:
    raise NotImplementedError()
