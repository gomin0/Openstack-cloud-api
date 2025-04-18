from pydantic import BaseModel, Field


class CreateVolumeRequest(BaseModel):
    name: str = Field(max_length=255, description="Name of volume", examples=["volume-001"])
    description: str = Field(max_length=255, description="Description of volume", examples=["For test"])
    size: int = Field(description="용량(GiB)", examples=[1])
    type_id: str = Field(
        min_length=36,
        max_length=36,
        description="사용할 volume type의 uuid",
        examples=["64abcd22-a30b-4982-8f82-332e89ff4bf7"]
    )
    image_id: str = Field(
        min_length=36,
        max_length=36,
        description="사용할 부팅 이미지의 uuid",
        examples=["1abc7a2f-8eec-49a2-b9ef-be16e0959cdb"]
    )


class UpdateVolumeInfoRequest(BaseModel):
    name: str = Field(max_length=255, description="Name of volume", examples=["volume-001"])
    description: str = Field(max_length=255, description="Description of volume", examples=["For test"])


class UpdateVolumeSizeRequest(BaseModel):
    size: int = Field(description="변경하려는 용량(GiB). 반드시 기존 용량보다 커야 합니다.", examples=[4])
