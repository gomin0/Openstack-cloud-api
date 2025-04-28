from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from domain.floating_ip.entity import FloatingIp
from domain.floating_ip.enum import FloatingIpStatus
from domain.server.entity import Server


class ServerResponse(BaseModel):
    id: int = Field(description="서버 ID", examples=[1])
    name: str = Field(description="서버 이름", examples=["server"])

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, server: Server | None) -> "ServerResponse":
        return cls.model_validate(server)


class FloatingIpResponse(BaseModel):
    id: int = Field(description="플로팅 IP ID", examples=[1])
    address: str = Field(description="IP 주소", examples=["0.0.0.0"])
    server_id: int | None = Field(default=None, description="서버 ID", examples=[1])
    project_id: int = Field(description="프로젝트 ID", examples=[1])
    status: FloatingIpStatus = Field(description="플로팅 IP 상태", examples=["ACTIVE"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)


class FloatingIpDetailResponse(BaseModel):
    id: int = Field(description="플로팅 IP ID", examples=[1])
    address: str = Field(description="IP 주소", examples=["0.0.0.0"])
    project_id: int = Field(description="프로젝트 ID", examples=[1])
    status: FloatingIpStatus = Field(description="플로팅 IP 상태", examples=["ACTIVE"])
    server: ServerResponse | None = Field(default=None, description="연결된 서버 정보")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_entity(cls, floating_ip: FloatingIp) -> "FloatingIpDetailResponse":
        server: Server = await floating_ip.server
        return cls(
            id=floating_ip.id,
            address=floating_ip.address,
            project_id=floating_ip.project_id,
            status=floating_ip.status,
            server=ServerResponse.from_entity(server) if server else None,
            created_at=floating_ip.created_at,
            updated_at=floating_ip.updated_at,
            deleted_at=floating_ip.deleted_at
        )


class FloatingIpDetailsResponse(BaseModel):
    floating_ips: list[FloatingIpDetailResponse]
