from fastapi import APIRouter, Depends, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.network_interface.service import NetworkInterfaceService
from common.infrastructure.async_client import get_async_client
from common.infrastructure.database import get_db_session
from common.util.auth_token_manager import get_current_user
from common.util.compensating_transaction import compensating_transaction
from common.util.context import CurrentUser

router = APIRouter(prefix="/network-interfaces", tags=["network-interface"])


@router.post(
    path="/{network_interface_id}/floating-ips/{floating_ip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="network interface 에 floating ip 연결",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "network interface 에 대한 접근 권한이 없는 경우"},
        404: {"description": "자원을 찾을 수 없는 경우"},
        409: {"description": "network interface 에 이미 연결된 floating ip인 경우"},
    }
)
async def attach_floating_ip_to_network_interface(
    network_interface_id: int,
    floating_ip_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    network_interface_service: NetworkInterfaceService = Depends(),
) -> None:
    async with compensating_transaction() as compensating_tx:
        await network_interface_service.attach_floating_ip_to_network_interface(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
            keystone_token=current_user.keystone_token,
            project_id=current_user.project_id,
            floating_ip_id=floating_ip_id,
            network_interface_id=network_interface_id,
        )


@router.delete(
    path="/{network_interface_id}/floating-ips/{floating_ip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="network interface에 floating ip 연결 해제",
    responses={
        400: {"description": "요청한 network interface 가 floating ip가 연결된 network interface 와 다른 경우"},
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "network interface 에 대한 접근 권한이 없는 경우"},
        404: {"description": "자원을 찾을 수 없는 경우"},
        409: {"description": "network interface 에 연결되어 있는 floating ip가 아닌 경우"},
    }
)
async def detach_floating_ip_from_network_interface(
    network_interface_id: int,
    floating_ip_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    network_interface_service: NetworkInterfaceService = Depends(),
) -> None:
    async with compensating_transaction() as compensating_tx:
        await network_interface_service.detach_floating_ip_from_network_interface(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
            keystone_token=current_user.keystone_token,
            project_id=current_user.project_id,
            floating_ip_id=floating_ip_id,
            network_interface_id=network_interface_id
        )
