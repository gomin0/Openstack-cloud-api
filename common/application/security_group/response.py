from datetime import datetime

from pydantic import Field, BaseModel, ConfigDict

from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.dto import SecurityGroupRuleDTO
from common.domain.security_group.entity import SecurityGroup
from common.domain.security_group.enum import SecurityGroupRuleDirection, SecurityGroupRuleEtherType
from common.domain.server.entity import Server


class SecurityGroupRuleResponse(BaseModel):
    openstack_id: str = Field(description="룰셋 ID")
    protocol: str | None = Field(default=None, description="프로토콜", examples=["tcp"])
    ether_type: SecurityGroupRuleEtherType = Field(description="인터넷 프로토콜 버전", examples=["IPv4"])
    direction: SecurityGroupRuleDirection = Field(description="방향", examples=["ingress"])
    port_range_min: int | None = Field(default=None, description="시작 포트", examples=[22])
    port_range_max: int | None = Field(default=None, description="종료 포트", examples=[22])
    remote_ip_prefix: str | None = Field(default=None, description="CIDR", examples=["0.0.0.0/0"])

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, security_group_rule: SecurityGroupRuleDTO) -> "SecurityGroupRuleResponse":
        return cls.model_validate(security_group_rule)


class ServerResponse(BaseModel):
    id: int = Field(description="서버 ID", examples=[1])
    name: str = Field(description="서버 이름", examples=["server"])

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, server: Server) -> "ServerResponse":
        return cls.model_validate(server)


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
        rules: list[SecurityGroupRuleDTO]
    ) -> "SecurityGroupDetailResponse":
        network_interfaces: list[NetworkInterface] = await security_group.network_interfaces
        servers: set = {await network_interface.server for network_interface in network_interfaces}
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
