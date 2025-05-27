from datetime import datetime, timezone
from logging import getLogger, Logger

from httpx import AsyncClient, Response, HTTPStatusError

from common.domain.keystone.model import KeystoneToken
from common.infrastructure.async_client import get_async_client
from common.util.envs import get_envs, Envs

envs: Envs = get_envs()
logger: Logger = getLogger(__name__)

_admin_keystone_token: KeystoneToken | None = None


def get_system_keystone_token() -> str:
    global _admin_keystone_token
    if _admin_keystone_token is None:
        raise ValueError("Admin keystone token is not set")
    return _admin_keystone_token.token


async def refresh_system_keystone_token() -> None:
    logger.info(f"Refreshing system keystone token at {datetime.now(timezone.utc)}")

    global _admin_keystone_token
    client: AsyncClient = get_async_client()

    response: Response = await client.post(
        url=f"{envs.OPENSTACK_SERVER_URL}:{envs.KEYSTONE_PORT}/v3/auth/tokens",
        headers={"Content-Type": "application/json"},
        json={
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "id": envs.CLOUD_ADMIN_OPENSTACK_ID,
                            "domain": {
                                "id": envs.DEFAULT_DOMAIN_OPENSTACK_ID
                            },
                            "password": envs.CLOUD_ADMIN_PASSWORD
                        }
                    }
                },
                "scope": {
                    "project": {
                        "id": envs.CLOUD_ADMIN_DEFAULT_PROJECT_OPENSTACK_ID
                    }
                }
            }
        }
    )
    try:
        response.raise_for_status()
    except HTTPStatusError as ex:
        logger.error(f"Failed to refresh system keystone token. ex={ex}")
        return

    _admin_keystone_token = KeystoneToken.from_token(
        token=response.headers.get("x-subject-token"),
        expires_at=response.json().get("token").get("expires_at")
    )
