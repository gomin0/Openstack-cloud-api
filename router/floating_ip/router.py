from fastapi import APIRouter, Query

from domain.enum import SortOrder
from router.floating_ip.request import CreateFloatingIPRequest
from router.floating_ip.response import FloatingIpDetailResponses, FloatingIpDetailResponse, FloatingIpResponse

router = APIRouter(prefix="/floating-ip", tags=["floating-ip"])


@router.get(
    "",
    status_code=200,
    summary="소유한 플로팅 IP 목록 조회",
    responses={
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"},
    }
)
async def find_floating_ips(
    sort_by: FloatingIPSortOption = Query(default=FloatingIPSortOption.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.ASC),
) -> FloatingIpDetailResponses:
    raise NotImplementedError()


@router.get(
    "/{floating_ip_id}",
    status_code=200,
    summary="단일 플로팅 IP 조회",
    responses={
        404: {"description": "해당 ID의 플로팅 IP를 찾을 수 없는 경우"},
    }
)
async def get_floating_ip(
    floating_ip_id: int,
) -> FloatingIpDetailResponse:
    raise NotImplementedError()


@router.post(
    "",
    status_code=201,
    summary="플로팅 IP 할당",
    responses={
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def create_floating_ip(
    request: CreateFloatingIPRequest,
) -> FloatingIpResponse:
    raise NotImplementedError()


@router.delete(
    "/{floating_ip_id}",
    status_code=204,
    summary="플로팅 IP 할당 해제(삭제)",
    responses={
        404: {"description": "해당 ID의 플로팅 IP를 찾을 수 없는 경우"},
        409: {"description": "서버에 연결된 상태에서는 삭제할 수 없음"},
    }
)
async def delete_floating_ip(
    floating_ip_id: int,
) -> None:
    raise NotImplementedError()
