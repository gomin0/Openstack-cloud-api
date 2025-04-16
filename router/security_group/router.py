from fastapi import APIRouter, Query

from domain.enum import SortOrder
from router.security_group.response import SecurityGroupDetailResponses, SecurityGroupDetailResponse

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


@router.get(
    "/{security_group_id}",
    status_code=200,
    summary="보안그룹 단일 조회",
    responses={
        404: {"description": "해당 ID의 보안그룹을 찾을 수 없는 경우"}
    }
)
async def get_security_group(
    security_group_id: int,
) -> SecurityGroupDetailResponse:
    raise NotImplementedError()
