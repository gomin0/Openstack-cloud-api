from pydantic import BaseModel, Field


class CreateFloatingIPRequest(BaseModel):
    project_id: int = Field(description="플로팅 IP를 할당할 프로젝트 ID", examples=[1])
    public_network_id: str = Field(description="플로팅 IP를 할당받을 공개 네트워크 ID", examples=["123"])
