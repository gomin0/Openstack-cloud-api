from datetime import datetime

from pydantic import BaseModel, Field


class DomainResponse(BaseModel):
    id: int = Field(description="도메인 ID", examples=[1])
    openstack_id: str = Field(description="오픈스택 리소스 id", examples=["779b35a7173444e387a7f34134a56e31"])
    name: str = Field(description="도메인 이름", examples=["example domain"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")
