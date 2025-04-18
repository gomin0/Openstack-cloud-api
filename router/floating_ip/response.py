from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from domain.floating_ip.enum import FloatingIpStatus


class ServerResponse(BaseModel):
    id: int = Field(description="서버 ID", examples=[1])
    name: str = Field(description="서버 이름", examples=["server"])

    model_config = ConfigDict(from_attributes=True)


class FloatingIpDetailResponse(BaseModel):
    id: int = Field(description="플로팅 IP ID", examples=[1])
    address: str = Field(description="IP 주소", examples=["0.0.0.0"])
    project_id: int = Field(description="프로젝트 ID", examples=[1])
    status: FloatingIpStatus = Field(description="플로팅 IP 상태", examples=["ACTIVE"])
    server: ServerResponse | None = Field(default=None, description="연결된 서버 정보")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")

    model_config = ConfigDict(from_attributes=True)


class FloatingIpDetailsResponse(BaseModel):
    floating_ips: list[FloatingIpDetailResponse]
