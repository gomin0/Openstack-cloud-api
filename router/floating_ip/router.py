from fastapi import APIRouter, Query

from domain.enum import SortOrder
from router.floating_ip.response import FloatingIpDetailResponses

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
