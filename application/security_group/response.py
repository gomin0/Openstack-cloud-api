from datetime import datetime

from pydantic import Field, BaseModel, ConfigDict

from domain.security_group.entity import SecurityGroup
from domain.security_group.enum import SecurityGroupRuleDirection
from domain.server.entity import Server


class SecurityGroupRuleResponse(BaseModel):
    id: str = Field(description="룰셋 ID")
    protocol: str | None = Field(default=None, description="프로토콜", examples=["tcp"])
    direction: SecurityGroupRuleDirection = Field(description="방향", examples=["ingress"])
    port_range_min: int | None = Field(default=None, description="시작 포트", examples=[22])
    port_range_max: int | None = Field(default=None, description="종료 포트", examples=[22])
    remote_ip_prefix: str | None = Field(default=None, description="CIDR", examples=["0.0.0.0/0"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, data: dict) -> "SecurityGroupRuleResponse":
        return cls(
            id=data["id"],
            protocol=data.get("protocol"),
            direction=data["direction"],
            port_range_min=data.get("port_range_min"),
            port_range_max=data.get("port_range_max"),
            remote_ip_prefix=data.get("remote_ip_prefix"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


class ServerResponse(BaseModel):
    id: int = Field(description="서버 ID", examples=[1])
    name: str = Field(description="서버 이름", examples=["server"])

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, server: Server) -> "ServerResponse":
        return cls(
            id=server.id,
            name=server.name
        )


class SecurityGroupDetailResponse(BaseModel):
    id: int = Field(description="보안그룹 ID")
    name: str = Field(description="보안그룹 이름")
    description: str | None = Field(description="보안그룹 설명")
    project_id: int = Field(description="소속 프로젝트 ID")
    rules: list[SecurityGroupRuleResponse] = Field(description="보안 그룹 룰셋 목록")
    servers: list[ServerResponse] = Field(description="연결된 서버 목록")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_entity(
        cls,
        security_group: SecurityGroup,
        rules: list[dict]
    ) -> "SecurityGroupDetailResponse":
        servers: list[Server] = await security_group.servers
        return cls(
            id=security_group.id,
            name=security_group.name,
            description=security_group.description,
            project_id=security_group.project_id,
            rules=[SecurityGroupRuleResponse.from_entity(rule) for rule in rules],
            servers=[ServerResponse.from_entity(server) for server in servers],
            created_at=security_group.created_at,
            updated_at=security_group.updated_at,
            deleted_at=security_group.deleted_at,
        )


class SecurityGroupDetailsResponse(BaseModel):
    security_groups: list[SecurityGroupDetailResponse]
