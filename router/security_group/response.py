from datetime import datetime

from pydantic import Field, BaseModel, ConfigDict

from domain.security_group.enum import SecurityGroupRuleDirection


class SecurityGroupRuleResponse(BaseModel):
    id: int = Field(description="룰셋 ID", examples=[1])
    protocol: str | None = Field(description="프로토콜", examples=["tcp"])
    direction: SecurityGroupRuleDirection = Field(description="방향", examples=["ingress"])
    port_range_min: int = Field(default=None, description="시작 포트", examples=[22])
    port_range_max: int = Field(default=None, description="종료 포트", examples=[22])
    remote_ip_prefix: str | None = Field(default=None, description="CIDR", examples=["0.0.0.0/0"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)


class ServerResponse(BaseModel):
    id: int = Field(description="서버 ID", examples=[1])
    name: str = Field(description="서버 이름", examples=["server"])

    model_config = ConfigDict(from_attributes=True)


class SecurityGroupDetailResponse(BaseModel):
    id: int = Field(description="보안그룹 ID")
    name: str = Field(description="보안그룹 이름")
    description: str = Field(description="보안그룹 설명")
    project_id: int = Field(description="소속 프로젝트 ID")
    rules: list[SecurityGroupRuleResponse] = Field(description="보안 그룹 룰셋 목록")
    servers: list[ServerResponse] = Field(description="연결된 서버 목록")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)


class SecurityGroupDetailsResponse(BaseModel):
    security_groups: list[SecurityGroupDetailResponse]
