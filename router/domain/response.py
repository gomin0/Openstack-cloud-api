from pydantic import BaseModel, Field


class DomainResponse(BaseModel):
    id: int = Field(description="도메인 ID", examples=[1])
    name: str = Field(description="도메인 이름", examples=["ted-domain"])
