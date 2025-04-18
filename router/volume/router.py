from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK, HTTP_202_ACCEPTED

from common.auth_token_manager import get_current_user
from common.context import CurrentUser
from router.volume.request import CreateVolumeRequest, UpdateVolumeInfoRequest, UpdateVolumeSizeRequest
from router.volume.response import VolumesDetailResponse, VolumeResponse, VolumeDetailResponse

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


@router.post(
    path="",
    status_code=HTTP_202_ACCEPTED,
    summary="볼륨 생성",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def create_volume(
    request: CreateVolumeRequest,
    _: CurrentUser = Depends(get_current_user),
) -> VolumeResponse:
    raise NotImplementedError()


@router.put(
    path="/{volume_id}/info",
    status_code=HTTP_200_OK,
    summary="볼륨 정보 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "볼륨에 대한 접근 권한이 없는 경우"},
        404: {"description": "볼륨을 찾을 수 없는 경우"},
        409: {"description": "변경하려는 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def update_volume_info(
    volume_id: int,
    request: UpdateVolumeInfoRequest,
    _: CurrentUser = Depends(get_current_user),
) -> VolumeResponse:
    raise NotImplementedError()


@router.put(
    path="/{volume_id}/size",
    status_code=HTTP_202_ACCEPTED,
    summary="볼륨 용량 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "볼륨에 대한 접근 권한이 없는 경우"},
        404: {"description": "볼륨을 찾을 수 없는 경우"},
        409: {"description": "변경하려는 볼륨 용량이 기존 용량보다 크지 않은 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def update_volume_size(
    volume_id: int,
    request: UpdateVolumeSizeRequest,
    _: CurrentUser = Depends(get_current_user),
) -> VolumeResponse:
    raise NotImplementedError()
