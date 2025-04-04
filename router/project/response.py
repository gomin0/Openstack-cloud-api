from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from domain.project.entity import Project


class DomainResponse(BaseModel):
    id: int = Field(description="도메인 ID", examples=[1])
    openstack_id: str = Field(description="오픈스택 리소스 id", examples=["779b35a7173444e387a7f34134a56e31"])
    name: str = Field(description="도메인 이름", examples=["example domain"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)


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


class ProjectResponse(BaseModel):
    id: int = Field(description="프로젝트 id", examples=[1])
    openstack_id: str = Field(description="프로젝트 uuid", examples=["779b35a7173444e387a7f34134a56e31"])
    name: str = Field(description="프로젝트 이름")
    domain_id: int = Field(description="프로젝트가 속한 도메인 정보")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_entity(cls, project: Project) -> "ProjectResponse":
        return cls.model_validate(project)


class ProjectDetailResponse(BaseModel):
    id: int = Field(description="프로젝트 id", examples=[1])
    openstack_id: str = Field(description="프로젝트 uuid", examples=["779b35a7173444e387a7f34134a56e31"])
    name: str = Field(description="프로젝트 이름")
    domain: DomainResponse = Field(description="프로젝트가 속한 도메인 정보")
    accounts: list[UserResponse] = Field(alias="users", description="프로젝트에 속한 계정 목록")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_entity(cls, project: Project) -> "ProjectDetailResponse":
        return cls(
            id=project.id,
            openstack_id=project.openstack_id,
            name=project.name,
            domain=DomainResponse.model_validate(project._domain),
            users=[UserResponse.model_validate(link._user) for link in project._linked_users],
            created_at=project.created_at,
            updated_at=project.updated_at,
            deleted_at=project.deleted_at,
        )


class ProjectListResponse(BaseModel):
    projects: list[ProjectDetailResponse] = Field(description="프로젝트 목록")
