from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from common.auth_token_manager import get_current_user
from common.context import CurrentUser
from router.volume.response import VolumesDetailResponse, VolumeDetailResponse

router = APIRouter(prefix="/volumes", tags=["volume"])


@router.get(
    path="",
    status_code=HTTP_200_OK,
    summary="볼륨 목록 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def find_volumes_detail(
    _: CurrentUser = Depends(get_current_user)
) -> VolumesDetailResponse:
    raise NotImplementedError()


@router.get(
    path="/{volume_id}",
    status_code=HTTP_200_OK,
    summary="볼륨 단건 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "볼륨에 대한 접근 권한이 없는 경우"},
        404: {"description": "볼륨을 찾을 수 없는 경우"},
    }
)
async def get_volume_detail(
    volume_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> VolumeDetailResponse:
    raise NotImplementedError()
