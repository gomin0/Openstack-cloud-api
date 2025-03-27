from pydantic import BaseModel, Field

from router.user.response import UserResponse


class LoginResponse(BaseModel):
    user: UserResponse = Field(description="로그인한 유저 정보")
