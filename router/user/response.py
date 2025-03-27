from datetime import datetime

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: int = Field(description="id", examples=["1"])
    openstack_id: str = Field(description="오픈스택 리소스 id", examples=["779b35a7173444e387a7f34134a56e31"])
    domain_id: int = Field(description="소속된 도메인의 id", examples=["1"])
    account_id: str = Field(description="로그인 id", examples=["woody0105"])
    name: str = Field(description="이름", examples=["woody"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")


class UserListResponse(BaseModel):
    users: list[UserResponse]
