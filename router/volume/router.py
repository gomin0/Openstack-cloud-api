from fastapi import APIRouter, Depends, Query, BackgroundTasks
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT

from application.volume.response import VolumesDetailResponse, VolumeResponse, VolumeDetailResponse
from application.volume.service import VolumeService
from common.auth_token_manager import get_current_user
from common.background_task_runner import run_background_task
from common.context import CurrentUser
from domain.enum import SortOrder
from domain.volume.enum import VolumeSortOption
from infrastructure.async_client import get_async_client
from infrastructure.database import get_db_session
from router.volume.request import CreateVolumeRequest, UpdateVolumeInfoRequest, UpdateVolumeSizeRequest

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
    sort_by: VolumeSortOption = Query(default=VolumeSortOption.CREATED_AT),
    sort_order: SortOrder = Query(default=SortOrder.ASC),
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
        409: {"description": "사용하려는 볼륨 이름이 이미 사용중인 볼륨 이름인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def create_volume(
    request: CreateVolumeRequest,
    background_tasks: BackgroundTasks,
    request_user: CurrentUser = Depends(get_current_user),
    volume_service: VolumeService = Depends(),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
) -> VolumeResponse:
    volume: VolumeResponse = await volume_service.create_volume(
        request_user=request_user,
        name=request.name,
        description=request.description,
        size=request.size,
        volume_type_openstack_id=request.volume_type_id,
        image_openstack_id=request.image_id,
        session=session,
        client=client,
    )
    run_background_task(
        background_tasks,
        volume_service.sync_creating_volume_until_available,
        keystone_token=request_user.keystone_token,
        project_openstack_id=request_user.project_openstack_id,
        volume_openstack_id=volume.openstack_id,
    )
    return volume


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
        400: {"description": "변경하려는 볼륨 용량이 기존 용량보다 크지 않은 경우"},
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "볼륨에 대한 접근 권한이 없는 경우"},
        404: {"description": "볼륨을 찾을 수 없는 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def update_volume_size(
    volume_id: int,
    request: UpdateVolumeSizeRequest,
    _: CurrentUser = Depends(get_current_user),
) -> VolumeResponse:
    raise NotImplementedError()


@router.delete(
    path="/{volume_id}",
    status_code=HTTP_204_NO_CONTENT,
    summary="볼륨 삭제",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "볼륨에 대한 접근 권한이 없는 경우"},
        404: {"description": "볼륨을 찾을 수 없는 경우"},
        409: {"description": "볼륨에 연결된 서버가 존재하거나, 볼륨이 삭제 가능한 상태가 아닌 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def delete_volume(
    volume_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()
