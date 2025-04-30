from fastapi import APIRouter, Query, Depends

from api_server.router.server.request import UpdateServerInfoRequest, CreateServerRequest
from common.application.server.response import ServerResponse, ServerDetailResponse, ServerDetailsResponse, \
    ServerVncUrlResponse
from common.domain.enum import SortOrder
from common.domain.server.enum import ServerSortOption, ServerStatus
from common.util.auth_token_manager import get_current_user
from common.util.context import CurrentUser

router = APIRouter(prefix="/servers", tags=["server"])


@router.get(
    "", status_code=200,
    summary="서버 목록 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "쿼리 파라미터 값이나 형식이 잘못된 경우"}
    }
)
async def find_servers(
    ids: list[int] | None = Query(default=None, description="ID 검색"),
    is_exclude_ids: bool = Query(default=False, description="ID 포함 검색, 제외 검색 여부"),
    name: str | None = Query(default=None, description="이름 검색"),
    sort_by: ServerSortOption = Query(default=ServerSortOption.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.DESC),
    _: CurrentUser = Depends(get_current_user),
) -> ServerDetailsResponse:
    raise NotImplementedError()


@router.get(
    "/{server_id}", status_code=200,
    summary="서버 단일 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버 접근 권한이 없는 경우"},
        404: {"description": "해당 ID의 서버를 찾을 수 없는 경우"}
    }
)
async def find_servers(
    server_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> ServerDetailResponse:
    raise NotImplementedError()


@router.post(
    path="", status_code=202,
    summary="서버 생성",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        409: {"description": "사용하려는 서버 이름이 이미 사용중인 이름인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def create_server(
    request: CreateServerRequest,
    _: CurrentUser = Depends(get_current_user),
) -> ServerResponse:
    raise NotImplementedError()


@router.put(
    path="/{server_id}/info",
    status_code=200,
    summary="서버 정보 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
        409: {"description": "변경하려는 이름이 이미 사용중인 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def update_server_info(
    server_id: int,
    request: UpdateServerInfoRequest,
    _: CurrentUser = Depends(get_current_user),
) -> ServerResponse:
    raise NotImplementedError()


@router.delete(
    path="/{server_id}",
    status_code=204,
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
    status_code=202,
    summary="서버 상태 변경",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
        409: {"description": "서버를 시작/정지할 수 없는 상태인 경우"},
    }
)
async def update_server_status(
    server_id: int,
    action: ServerStatus = Query(description="서버 시작(ACTIVE) or 정지(SHUTOFF)"),
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()


@router.get(
    path="/{server_id}/vnc-url",
    status_code=200,
    summary="서버 VNC 접속 기능(링크) 제공",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "서버를 찾을 수 없는 경우"},
    }
)
async def get_server_vnc_url(
    server_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> ServerVncUrlResponse:
    raise NotImplementedError()


@router.post(
    path="/{server_id}/volumes/{volume_id}",
    status_code=200,
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
    status_code=202,
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


@router.post(
    path="/{server_id}/floating-ips/{floating_ip_id}",
    status_code=200,
    summary="서버에 floating ip 연결",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "자원을 찾을 수 없는 경우"},
        409: {"description": "서버에 연결할 수 없는 floating ip인 경우"},
    }
)
async def attach_floating_ip_to_server(
    server_id: int,
    floating_ip_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()


@router.delete(
    path="/{server_id}/floating-ips/{volume_id}",
    status_code=200,
    summary="서버에 floating ip 연결 해제",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        403: {"description": "서버에 대한 접근 권한이 없는 경우"},
        404: {"description": "자원을 찾을 수 없는 경우"},
        409: {"description": "서버에 연결되어 있는 floating ip가 아닌 경우"},
    }
)
async def detach_floating_ip_from_server(
    server_id: int,
    floating_ip_id: int,
    _: CurrentUser = Depends(get_current_user),
) -> None:
    raise NotImplementedError()
