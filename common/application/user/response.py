from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from common.domain.domain.entity import Domain
from common.domain.project.entity import Project
from common.domain.user.entity import User


class DomainResponse(BaseModel):
    id: int = Field(description="도메인 ID", examples=[1])
    openstack_id: str = Field(description="오픈스택 리소스 id", examples=["779b35a7173444e387a7f34134a56e31"])
    name: str = Field(description="도메인 이름", examples=["example domain"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, domain: Domain) -> "DomainResponse":
        return cls.model_validate(domain)


class ProjectResponse(BaseModel):
    id: int = Field(description="프로젝트 id", examples=[1])
    openstack_id: str = Field(description="프로젝트 uuid", examples=["779b35a7173444e387a7f34134a56e31"])
    domain_id: int = Field(description="프로젝트가 속한 도메인 정보")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, project: Project) -> "ProjectResponse":
        return cls.model_validate(project)


class UserResponse(BaseModel):
    id: int = Field(description="id", examples=["1"])
    openstack_id: str = Field(description="오픈스택 리소스 id", examples=["779b35a7173444e387a7f34134a56e31"])
    domain_id: int = Field(description="소속된 도메인의 id", examples=["1"])
    account_id: str = Field(description="로그인 id", examples=["woody0105"])
    name: str = Field(description="이름", examples=["woody"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        return cls.model_validate(user)


class UserDetailResponse(BaseModel):
    id: int = Field(description="id", examples=["1"])
    openstack_id: str = Field(description="오픈스택 리소스 id", examples=["779b35a7173444e387a7f34134a56e31"])
    domain: DomainResponse = Field(description="소속된 도메인")
    projects: list[ProjectResponse] = Field(description="소속된 프로젝트 목록")
    account_id: str = Field(description="로그인 id", examples=["woody0105"])
    name: str = Field(description="이름", examples=["woody"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_entity(cls, user: User) -> "UserDetailResponse":
        projects: list[Project] = await user.projects
        domain: Domain = await user.domain
        return cls(
            id=user.id,
            openstack_id=user.openstack_id,
            domain=DomainResponse.from_entity(domain),
            projects=[ProjectResponse.from_entity(project) for project in projects],
            account_id=user.account_id,
            name=user.name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
        )


class UserDetailsResponse(BaseModel):
    users: list[UserDetailResponse]
