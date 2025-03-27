from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from router.domain.response import DomainResponse
from router.user.response import UserResponse


class ProjectResponse(BaseModel):
    id: int = Field(description="프로젝트 id", examples=[1])
    openstack_id: str = Field(description="프로젝트 uuid", examples=["779b35a7173444e387a7f34134a56e31"])
    domain_id: int = Field(description="프로젝트가 속한 도메인 정보")
    created_at: datetime = Field(description="생성일", examples=["2025-03-027T00:00:00"])
    updated_at: datetime = Field(description="생성일", examples=["2025-03-027T00:00:00"])
    deleted_at: datetime | None = Field(None, description="생성일", examples=["2025-03-027T00:00:00"])


class ProjectDetailResponse(BaseModel):
    id: int = Field(description="프로젝트 id", examples=[1])
    openstack_id: str = Field(description="프로젝트 uuid", examples=["779b35a7173444e387a7f34134a56e31"])
    domain: DomainResponse = Field(description="프로젝트가 속한 도메인 정보")
    accounts: List[UserResponse] = Field(description="프로젝트에 속한 계정 목록")
    created_at: datetime = Field(description="생성일", examples=["2025-03-027T00:00:00"])
    updated_at: datetime = Field(description="생성일", examples=["2025-03-027T00:00:00"])
    deleted_at: datetime | None = Field(None, description="생성일", examples=["2025-03-027T00:00:00"])


class ProjectListResponse(BaseModel):
    projects: List[ProjectDetailResponse] = Field(description="프로젝트 목록")
