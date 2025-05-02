from pydantic import BaseModel, Field

from common.domain.security_group.enum import SecurityGroupRuleDirection


class SecurityGroupRuleRequest(BaseModel):
    protocol: str | None = Field(max_length=10, default=None, description="프로토콜", examples=["tcp"])
    direction: SecurityGroupRuleDirection = Field(description="방향", examples=["ingress"])
    port_range_min: int | None = Field(default=None, description="시작 포트", examples=[22])
    port_range_max: int | None = Field(default=None, description="종료 포트", examples=[22])
    remote_ip_prefix: str | None = Field(max_length=43, default=None, description="CIDR", examples=["0.0.0.0/0"])


class CreateSecurityGroupRequest(BaseModel):
    name: str = Field(max_length=255, description="보안그룹 이름")
    description: str = Field(max_length=255, description="보안그룹 설명")
    rules: list[SecurityGroupRuleRequest] = Field(description="초기 룰셋 목록")


class UpdateSecurityGroupRequest(BaseModel):
    name: str = Field(max_length=255, description="변경할 보안그룹 이름")
    description: str = Field(max_length=255, description="변경할 보안그룹 설명")
    rules: list[SecurityGroupRuleRequest] = Field(description="전체 룰셋 목록 (기존 대체)")
