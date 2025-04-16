from fastapi import APIRouter, Query

from domain.enum import SortOrder
from router.security_group.response import SecurityGroupDetailResponses

router = APIRouter(prefix="/security-group", tags=["security-group"])


@router.get(
    "", status_code=200,
    summary="보안그룹 목록 조회",
    responses={
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"}
    }
)
async def find_security_groups(
    sort_by: SecurityGroupSortOption = Query(default=SecurityGroupSortOption.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.ASC),
) -> SecurityGroupDetailResponses:
    raise NotImplementedError()
