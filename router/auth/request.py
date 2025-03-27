from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    account_id: str = Field(max_length=15, description="로그인 id", examples=["woody0105"])
    password: str = Field(description="비밀번호", examples=["1q2w3e4r"])
