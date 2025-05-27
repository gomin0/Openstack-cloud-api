from pydantic import BaseModel, Field


class ProjectUpdateRequest(BaseModel):
    name: str = Field(min_length=2, description="새 프로젝트 이름", examples=["new-project-name"])
