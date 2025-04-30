from fastapi import APIRouter, Query, Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api_server.router.floating_ip.request import CreateFloatingIpRequest
from common.application.floating_ip.response import FloatingIpDetailsResponse, FloatingIpDetailResponse, \
    FloatingIpResponse
from common.application.floating_ip.service import FloatingIpService
from common.domain.enum import SortOrder
from common.domain.floating_ip.enum import FloatingIpSortOption
from common.infrastructure.async_client import get_async_client
from common.infrastructure.database import get_db_session
from common.util.auth_token_manager import get_current_user
from common.util.compensating_transaction import compensating_transaction
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
    current_user: CurrentUser = Depends(get_current_user),
    floating_ip_service: FloatingIpService = Depends(),
    session: AsyncSession = Depends(get_db_session)
) -> FloatingIpDetailsResponse:
    return await floating_ip_service.find_floating_ips_details(
        session=session,
        project_id=current_user.project_id,
        sort_by=sort_by,
        order=order
    )


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
    current_user: CurrentUser = Depends(get_current_user),
    floating_ip_service: FloatingIpService = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> FloatingIpDetailResponse:
    return await floating_ip_service.get_floating_ip_detail(
        session=session,
        project_id=current_user.project_id,
        floating_ip_id=floating_ip_id,
    )


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
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    floating_ip_service: FloatingIpService = Depends(),
) -> FloatingIpResponse:
    async with compensating_transaction() as compensating_tx:
        return await floating_ip_service.create_floating_ip(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
            project_id=current_user.project_id,
            keystone_token=current_user.keystone_token,
            floating_network_id=request.floating_network_id
        )


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
    current_user: CurrentUser = Depends(get_current_user),
    floating_ip_service: FloatingIpService = Depends(),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
) -> None:
    await floating_ip_service.delete_floating_ip(
        session=session,
        client=client,
        project_id=current_user.project_id,
        keystone_token=current_user.keystone_token,
        floating_ip_id=floating_ip_id,
    )
