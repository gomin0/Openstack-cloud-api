from fastapi import APIRouter, Query, Depends

from api_server.router.floating_ip.request import CreateFloatingIpRequest
from common.application.floating_ip.response import FloatingIpDetailsResponse, FloatingIpDetailResponse, \
    FloatingIpResponse
from common.domain.enum import SortOrder
from common.domain.floating_ip.enum import FloatingIpSortOption
from common.util.auth_token_manager import get_current_user
from common.util.context import CurrentUser

router = APIRouter(prefix="/floating-ips", tags=["floating-ip"])


@router.get(
    "",
    status_code=200,
    summary="소유한 플로팅 IP 목록 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"},
    }
)
async def find_floating_ips(
    sort_by: FloatingIpSortOption = Query(default=FloatingIpSortOption.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.ASC),
    _: CurrentUser = Depends(get_current_user),
) -> FloatingIpDetailsResponse:
    raise NotImplementedError()


@router.get(
    "/{floating_ip_id}",
    status_code=200,
    summary="단일 플로팅 IP 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "floating ip에 대한 접근 권한이 없는 경우"},
        404: {"description": "해당 ID의 플로팅 IP를 찾을 수 없는 경우"},
    }
)
async def get_floating_ip(
    floating_ip_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> FloatingIpDetailResponse:
    raise NotImplementedError()


@router.post(
    "",
    status_code=201,
    summary="플로팅 IP 할당",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def create_floating_ip(
    request: CreateFloatingIpRequest,
    _: CurrentUser = Depends(get_current_user),
) -> FloatingIpResponse:
    raise NotImplementedError()


@router.delete(
    "/{floating_ip_id}",
    status_code=204,
    summary="플로팅 IP 할당 해제(삭제)",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "floating ip에 대한 접근 권한이 없는 경우"},
        404: {"description": "해당 ID의 플로팅 IP를 찾을 수 없는 경우"},
        409: {"description": "서버에 연결된 상태에서는 삭제할 수 없음"},
    }
)
async def delete_floating_ip(
    floating_ip_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()
