from fastapi import APIRouter, Query

from domain.enum import SortOrder
from domain.security_group.enum import SecurityGroupSortOption
from router.security_group.request import CreateSecurityGroupRequest, UpdateSecurityGroupRequest
from router.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse

router = APIRouter(prefix="/security-groups", tags=["security-group"])


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
) -> SecurityGroupDetailsResponse:
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


@router.post(
    "", status_code=201,
    summary="보안그룹 생성",
    responses={
        409: {"description": "보안그룹 이름이 이미 프로젝트 내에서 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def create_security_group(
    request: CreateSecurityGroupRequest,
) -> SecurityGroupDetailResponse:
    raise NotImplementedError()


@router.put(
    "/{security_group_id}",
    status_code=200,
    summary="보안그룹 변경",
    responses={
        404: {"description": "해당 ID의 보안그룹을 찾을 수 없는 경우"},
        409: {"description": "변경하려는 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def update_security_group(
    security_group_id: int,
    request: UpdateSecurityGroupRequest,
) -> SecurityGroupDetailResponse:
    raise NotImplementedError()


@router.delete(
    "/{security_group_id}",
    status_code=204,
    summary="보안그룹 삭제",
    responses={
        404: {"description": "해당 ID의 보안그룹을 찾을 수 없는 경우"},
        409: {"description": "연결된 서버가 존재해 삭제할 수 없는 경우"}
    }
)
async def delete_security_group(
    security_group_id: int,
) -> None:
    raise NotImplementedError()
