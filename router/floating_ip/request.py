from pydantic import BaseModel, Field


class CreateFloatingIPRequest(BaseModel):
    project_id: int = Field(description="플로팅 IP를 할당할 프로젝트 ID", examples=[1])
