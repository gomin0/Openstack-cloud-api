from fastapi import APIRouter, Query, Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.security_group.dto import SecurityGroupRuleDTO
from application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from application.security_group.service import SecurityGroupService
from common.auth_token_manager import get_current_user
from common.compensating_transaction import compensating_transaction
from common.context import CurrentUser
from domain.enum import SortOrder
from domain.security_group.enum import SecurityGroupSortOption
from infrastructure.async_client import get_async_client
from infrastructure.database import get_db_session
from router.security_group.request import CreateSecurityGroupRequest, UpdateSecurityGroupRequest

router = APIRouter(prefix="/security-groups", tags=["security-group"])


@router.get(
    "", status_code=200,
    summary="보안그룹 목록 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"}
    }
)
async def find_security_groups(
    sort_by: SecurityGroupSortOption = Query(default=SecurityGroupSortOption.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.ASC),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    security_group_service: SecurityGroupService = Depends(),
) -> SecurityGroupDetailsResponse:
    return await security_group_service.find_security_groups_details(
        session=session,
        client=client,
        project_id=current_user.project_id,
        project_openstack_id=current_user.project_openstack_id,
        keystone_token=current_user.keystone_token,
        sort_by=sort_by,
        sort_order=order,
        with_relations=True
    )


@router.get(
    "/{security_group_id}",
    status_code=200,
    summary="보안그룹 단일 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "보안 그룹 접근 권한이 없는 경우"},
        404: {"description": "해당 ID의 보안그룹을 찾을 수 없는 경우"}
    }
)
async def get_security_group(
    security_group_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    security_group_service: SecurityGroupService = Depends(),
) -> SecurityGroupDetailResponse:
    return await security_group_service.get_security_group(
        session=session,
        client=client,
        project_id=current_user.project_id,
        keystone_token=current_user.keystone_token,
        security_group_id=security_group_id
    )


@router.post(
    "", status_code=201,
    summary="보안그룹 생성",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        409: {"description": "보안그룹 이름이 이미 프로젝트 내에서 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def create_security_group(
    request: CreateSecurityGroupRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    security_group_service: SecurityGroupService = Depends(),
) -> SecurityGroupDetailResponse:
    rules = [
        SecurityGroupRuleDTO(
            protocol=rule.protocol,
            direction=rule.direction,
            port_range_min=rule.port_range_min,
            port_range_max=rule.port_range_max,
            remote_ip_prefix=rule.remote_ip_prefix
        )
        for rule in request.rules
    ]
    async with compensating_transaction() as compensating_tx:
        return await security_group_service.create_security_group(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
            keystone_token=current_user.keystone_token,
            project_id=current_user.project_id,
            name=request.name,
            description=request.description,
            rules=rules,
        )


@router.put(
    "/{security_group_id}",
    status_code=200,
    summary="보안그룹 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "보안 그룹 변경 권한이 없는 경우"},
        404: {"description": "해당 ID의 보안그룹을 찾을 수 없는 경우"},
        409: {"description": "변경하려는 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"}
    }
)
async def update_security_group(
    security_group_id: int,
    request: UpdateSecurityGroupRequest,
    _: CurrentUser = Depends(get_current_user),
) -> SecurityGroupDetailResponse:
    raise NotImplementedError()


@router.delete(
    "/{security_group_id}",
    status_code=204,
    summary="보안그룹 삭제",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "보안 그룹 삭제 권한이 없는 경우"},
        404: {"description": "해당 ID의 보안그룹을 찾을 수 없는 경우"},
        409: {"description": "연결된 서버가 존재해 삭제할 수 없는 경우"}
    }
)
async def delete_security_group(
    security_group_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()
