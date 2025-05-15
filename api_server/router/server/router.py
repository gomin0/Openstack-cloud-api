from typing import Annotated

from fastapi import APIRouter, Query, Depends, BackgroundTasks
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_204_NO_CONTENT, HTTP_200_OK, HTTP_202_ACCEPTED

from api_server.router.server.request import UpdateServerInfoRequest, CreateServerRequest
from common.application.server.response import (
    ServerResponse, ServerDetailResponse, ServerDetailsResponse, ServerVncUrlResponse
)
from common.application.server.service import ServerService
from common.domain.enum import SortOrder
from common.domain.server.enum import ServerSortOption, ServerStatus
from common.infrastructure.async_client import get_async_client
from common.infrastructure.database import get_db_session
from common.util.auth_token_manager import get_current_user
from common.util.background_task_runner import run_background_task
from common.util.compensating_transaction import compensating_transaction
from common.util.context import CurrentUser

router = APIRouter(prefix="/servers", tags=["server"])


@router.get(
    "", status_code=HTTP_200_OK,
    summary="서버 목록 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"}
    }
)
async def find_servers(
    id_: Annotated[int | None, Query(alias="id")] = None,
    ids_contain: Annotated[list[int] | None, Query()] = None,
    ids_exclude: Annotated[list[int] | None, Query()] = None,
    name_eq: str | None = None,
    name_like: str | None = None,
    sort_by: ServerSortOption = ServerSortOption.CREATED_AT,
    order: SortOrder = SortOrder.DESC,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    server_service: ServerService = Depends()
) -> ServerDetailsResponse:
    return await server_service.find_servers_details(
        session=session,
        id_=id_,
        ids_contain=ids_contain,
        ids_exclude=ids_exclude,
        name_eq=name_eq,
        name_like=name_like,
        sort_by=sort_by,
        order=order,
        project_id=current_user.project_id,
    )


@router.get(
    "/{server_id}", status_code=HTTP_200_OK,
    summary="서버 단일 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버 접근 권한이 없는 경우"},
        404: {"description": "해당 ID의 서버를 찾을 수 없는 경우"}
    }
)
async def get_server(
    server_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    server_service: ServerService = Depends()
) -> ServerDetailResponse:
    return await server_service.get_server_detail(
        session=session,
        server_id=server_id,
        project_id=current_user.project_id
    )


@router.post(
    path="", status_code=HTTP_202_ACCEPTED,
    summary="서버 생성",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        409: {"description": "사용하려는 서버 이름이 이미 사용중인 이름인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def create_server(
    request: CreateServerRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    server_service: ServerService = Depends(),
) -> ServerResponse:
    async with compensating_transaction() as compensating_tx:
        server: ServerResponse = await server_service.create_server(
            compensating_tx=compensating_tx,
            session=session,
            client=client,
            command=request.to_command(
                keystone_token=current_user.keystone_token,
                current_project_id=current_user.project_id,
                current_project_openstack_id=current_user.project_openstack_id,
            ),
        )
    run_background_task(
        background_task=background_tasks,
        task=server_service.finalize_server_creation,
        keystone_token=current_user.keystone_token,
        server_openstack_id=server.openstack_id,
        image_openstack_id=request.root_volume.image_id,
        root_volume_size=request.root_volume.size,
    )
    return server


@router.put(
    path="/{server_id}/info",
    status_code=HTTP_200_OK,
    summary="서버 정보 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 수정 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
        409: {"description": "변경하려는 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def update_server_info(
    server_id: int,
    request: UpdateServerInfoRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    server_service: ServerService = Depends(),
) -> ServerResponse:
    return await server_service.update_server_info(
        session=session,
        current_project_id=current_user.project_id,
        server_id=server_id,
        name=request.name,
        description=request.description,
    )


@router.delete(
    path="/{server_id}",
    status_code=HTTP_204_NO_CONTENT,
    summary="서버 삭제",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
        409: {"description": "서버가 삭제 가능한 상태가 아닌 경우"},
    }
)
async def delete_server(
    server_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()


@router.put(
    path="/{server_id}/status",
    status_code=HTTP_202_ACCEPTED,
    summary="서버 상태 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
        409: {"description": "서버를 시작/정지할 수 없는 상태인 경우"},
        422: {"description": "지원하지 않는 서버 상태인 경우"},
    }
)
async def update_server_status(
    server_id: int,
    status: Annotated[ServerStatus, Query(description="서버 시작(ACTIVE) or 정지(SHUTOFF)")],
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()


@router.get(
    path="/{server_id}/vnc-url",
    status_code=HTTP_200_OK,
    summary="서버 VNC 접속 기능(링크) 제공",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
    }
)
async def get_server_vnc_url(
    server_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    client: AsyncClient = Depends(get_async_client),
    server_service: ServerService = Depends(),
) -> ServerVncUrlResponse:
    server: ServerResponse = await server_service.get_server(
        session=session,
        server_id=server_id,
        project_id=current_user.project_id,
    )
    url: str = await server_service.get_vnc_console(
        client=client,
        keystone_token=current_user.keystone_token,
        server_openstack_id=server.openstack_id,
    )
    return ServerVncUrlResponse(url=url)


@router.post(
    path="/{server_id}/volumes/{volume_id}",
    status_code=HTTP_200_OK,
    summary="서버에 볼륨 연결",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "자원을 찾을 수 없는 경우"},
        409: {"description": "서버에 연결할 수 없는 볼륨인 경우"},
    }
)
async def attach_volume_to_server(
    server_id: int,
    volume_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()


@router.delete(
    path="/{server_id}/volumes/{volume_id}",
    status_code=HTTP_202_ACCEPTED,
    summary="서버에 볼륨 연결 해제",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "자원을 찾을 수 없는 경우"},
        409: {"description": "서버에 연결되어 있는 볼륨이 아닌 경우"},
    }
)
async def detach_volume_from_server(
    server_id: int,
    volume_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()
