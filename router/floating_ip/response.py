from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ServerResponse(BaseModel):
    id: int = Field(description="서버 ID", examples=[1])
    name: str = Field(description="서버 이름", examples=["my-server"])

    model_config = ConfigDict(from_attributes=True)


class FloatingIpResponse(BaseModel):
    id: int = Field(description="플로팅 IP ID", examples=[1])
    ip_address: str = Field(description="IP 주소", examples=["203.0.113.1"])
    project_id: int = Field(description="프로젝트 ID", examples=[10])
    status: FloatingIPStatus = Field(description="플로팅 IP 상태", examples=["ACTIVE"])
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)


class FloatingIpDetailResponse(BaseModel):
    id: int = Field(description="플로팅 IP ID", examples=[1])
    ip_address: str = Field(description="IP 주소", examples=["203.0.113.1"])
    project_id: int = Field(description="프로젝트 ID", examples=[10])
    status: FloatingIPStatus = Field(description="플로팅 IP 상태", examples=["ACTIVE"])
    server: ServerResponse | None = Field(default=None, description="연결된 서버 정보 (없을 수 있음)")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")
    deleted_at: datetime | None = Field(default=None, description="삭제일")

    model_config = ConfigDict(from_attributes=True)


class FloatingIpDetailResponses(BaseModel):
    floating_ips: list[FloatingIpDetailResponse]
