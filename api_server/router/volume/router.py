from fastapi import APIRouter, Depends, BackgroundTasks
from starlette.status import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT

from api_server.router.volume.request import CreateVolumeRequest, UpdateVolumeInfoRequest, UpdateVolumeSizeRequest
from common.application.volume.response import VolumeDetailsResponse, VolumeResponse, VolumeDetailResponse
from common.application.volume.service import VolumeService
from common.domain.enum import SortOrder
from common.domain.volume.enum import VolumeSortOption
from common.util.auth_token_manager import get_current_user
from common.util.context import CurrentUser

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
    sort_by: VolumeSortOption = VolumeSortOption.CREATED_AT,
    sort_order: SortOrder = SortOrder.ASC,
    current_user: CurrentUser = Depends(get_current_user),
    volume_service: VolumeService = Depends(),
) -> VolumeDetailsResponse:
    volume_details: list[VolumeDetailResponse] = await volume_service.find_volume_details(
        current_project_id=current_user.project_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return VolumeDetailsResponse(volumes=volume_details)


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
    current_user: CurrentUser = Depends(get_current_user),
    volume_service: VolumeService = Depends()
) -> VolumeDetailResponse:
    return await volume_service.get_volume_detail(
        current_project_id=current_user.project_id,
        volume_id=volume_id,
    )


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
) -> VolumeResponse:
    volume: VolumeResponse = await volume_service.create_volume(
        keystone_token=request_user.keystone_token,
        project_id=request_user.project_id,
        project_openstack_id=request_user.project_openstack_id,
        name=request.name,
        description=request.description,
        size=request.size,
        volume_type_openstack_id=request.volume_type_id,
        image_openstack_id=request.image_id,
    )
    background_tasks.add_task(
        func=volume_service.sync_creating_volume_until_available,
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
    request_user: CurrentUser = Depends(get_current_user),
    volume_service: VolumeService = Depends(),
) -> VolumeResponse:
    return await volume_service.update_volume_info(
        current_project_id=request_user.project_id,
        volume_id=volume_id,
        name=request.name,
        description=request.description,
    )


@router.put(
    path="/{volume_id}/size",
    status_code=HTTP_200_OK,
    summary="볼륨 용량 변경",
    description="""
        <p>볼륨 용량을 변경합니다. 
        <p>상태가 <code>AVAILABLE</code>인 볼륨만 용량을 변경할 수 있습니다.
        <p>용량은 상향 조정만 가능합니다.
    """,
    responses={
        400: {"description": "변경하려는 볼륨 용량이 기존 용량보다 크지 않은 경우"},
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "볼륨에 대한 접근 권한이 없는 경우"},
        404: {"description": "볼륨을 찾을 수 없는 경우"},
        409: {"description": "용량을 변경하려는 볼륨의 상태가 <code>AVAILABLE</code>이 아닌 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def update_volume_size(
    volume_id: int,
    request: UpdateVolumeSizeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    volume_service: VolumeService = Depends(),
) -> VolumeResponse:
    return await volume_service.update_volume_size(
        keystone_token=current_user.keystone_token,
        current_project_id=current_user.project_id,
        current_project_openstack_id=current_user.project_openstack_id,
        volume_id=volume_id,
        new_size=request.size,
    )


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
    current_user: CurrentUser = Depends(get_current_user),
    volume_service: VolumeService = Depends(),
) -> None:
    await volume_service.delete_volume(
        current_project_id=current_user.project_id,
        current_project_openstack_id=current_user.project_openstack_id,
        keystone_token=current_user.keystone_token,
        volume_id=volume_id,
    )
