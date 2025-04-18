from pydantic import BaseModel, Field


class CreateFloatingIPRequest(BaseModel):
    floating_network_openstack_id: str = Field(
        min_length=36,
        max_length=36,
        description="플로팅 IP를 할당할 프로젝트 ID",
        examples=["b1321e7e-7709-47d1-b851-5e6c4e0e1111"]
    )
