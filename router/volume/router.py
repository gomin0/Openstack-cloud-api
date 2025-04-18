from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from common.auth_token_manager import get_current_user
from common.context import CurrentUser
from router.volume.response import VolumesDetailResponse

router = APIRouter(prefix="/volumes", tags=["volume"])


@router.get(
    path="",
    status_code=HTTP_200_OK,
    summary="볼륨 목록 조회",
    responses={
        401: {"description": "인증 정보가 유효하지 않은 경우"},
        422: {"description": "요청 데이터의 값이나 형식이 잘못된 경우"},
    }
)
async def find_volumes_detail(
    _: CurrentUser = Depends(get_current_user)
) -> VolumesDetailResponse:
    raise NotImplementedError()
