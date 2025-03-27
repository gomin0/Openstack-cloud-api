from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class AccountInProject(BaseModel):
    id: int = Field(description="계정 ID", examples=[1])
    name: str = Field(description="계정 이름", examples=["ted"])


class DomainInProject(BaseModel):
    id: int = Field(description="도메인 ID", examples=[1])
    name: str = Field(description="도메인 이름", examples=["ted-domain"])


class ProjectResponse(BaseModel):
    id: int = Field(description="프로젝트 id", examples=[1])
    uuid: str = Field(description="프로젝트 uuid", examples=["779b35a7173444e387a7f34134a56e31"])
    domain: DomainInProject = Field(description="프로젝트가 속한 도메인 정보")
    accounts: List[AccountInProject] = Field(description="프로젝트에 속한 계정 목록")
    created_at: datetime = Field(description="생성일", examples=["2025-03-027T00:00:00"])
    updated_at: datetime = Field(description="생성일", examples=["2025-03-027T00:00:00"])
    deleted_at: datetime | None = Field(None, description="생성일", examples=["2025-03-027T00:00:00"])


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse] = Field(description="프로젝트 목록")
