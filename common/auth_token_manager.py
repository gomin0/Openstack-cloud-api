from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from common.context import CurrentUser
from common.envs import get_envs
from domain.keystone.model import KeystoneToken
from exception.auth_exception import InvalidAccessTokenException

envs = get_envs()

_JWT_SECRET_KEY = envs.JWT_SECRET
_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_DURATION_MINUTES = envs.ACCESS_TOKEN_DURATION_MINUTES


def create_access_token(
    user_id: int,
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
            "keystone": {
                "token": keystone_token.token,
                "exp": int(keystone_token.expires_at.timestamp()),
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
    payload = _decode_access_token(token=credentials.credentials)
    return CurrentUser(
        user_id=int(payload.get("sub")),
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
