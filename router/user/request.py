from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    account_id: str = Field(max_length=20, description="로그인 id", examples=["example1234"])
    password: str = Field(description="비밀번호", examples=["1q2w3e4r"])
    name: str = Field(max_length=15, description="이름", examples=["woody"])


class UpdateUserRequest(BaseModel):
    name: str = Field(max_length=15, description="이름", examples=["woody"])
