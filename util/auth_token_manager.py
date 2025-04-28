from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from domain.keystone.model import KeystoneToken
from exception.auth_exception import InvalidAccessTokenException
from util.context import CurrentUser
from util.envs import get_envs

envs = get_envs()

_JWT_SECRET_KEY = envs.JWT_SECRET
_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_DURATION_MINUTES = envs.ACCESS_TOKEN_DURATION_MINUTES


def create_access_token(
    user_id: int,
    user_openstack_id: str,
    project_id: int,
    project_openstack_id: str,
    keystone_token: KeystoneToken,
) -> str:
    now = datetime.now(tz=timezone.utc)
    issued_at: datetime = now
    expires_at: datetime = now + timedelta(minutes=_ACCESS_TOKEN_DURATION_MINUTES)

    buffered_exp = keystone_token.expires_at - timedelta(minutes=5)
    if expires_at > buffered_exp:
        expires_at = buffered_exp

    return jwt.encode(
        claims={
            "sub": str(user_id),
            "user": {
                "id": user_id,
                "openstack_id": user_openstack_id,
            },
            "project": {
                "id": project_id,
                "openstack_id": project_openstack_id,
            },
            "keystone": {
                "token": keystone_token.token,
                "expires_at": int(keystone_token.expires_at.timestamp()),
            },
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        key=_JWT_SECRET_KEY,
        algorithm=_JWT_ALGORITHM,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> CurrentUser:
    # TODO: 유저, 프로젝트 등 데이터 유효성 검증 로직 추가
    payload = _decode_access_token(token=credentials.credentials)
    return CurrentUser(
        user_id=int(payload.get("user").get("id")),
        user_openstack_id=payload.get("user").get("openstack_id"),
        project_id=int(payload.get("project").get("id")),
        project_openstack_id=payload.get("project").get("openstack_id"),
        keystone_token=payload.get("keystone").get("token"),
    )


def _decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token=token,
            key=_JWT_SECRET_KEY,
            algorithms=[_JWT_ALGORITHM]
        )
    except JWTError as e:
        raise InvalidAccessTokenException() from e
