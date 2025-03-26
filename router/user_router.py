from fastapi import APIRouter
from exception.user_exceptions import UserNotFoundException

router = APIRouter(
    prefix="/user",
)


# CustomException 확인용
@router.get("/{user_id}")
async def get_user(user_id):
    if user_id != "2":
        raise UserNotFoundException()
