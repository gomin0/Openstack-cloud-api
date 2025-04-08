from httpx import AsyncClient, Response

from common.envs import get_envs
from infrastructure.openstack_client import OpenStackClient

envs = get_envs()


class KeystoneClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _KEYSTONE_PORT: int = envs.KEYSTONE_PORT
    _KEYSTONE_URL: str = f"{_OPEN_STACK_URL}:{_KEYSTONE_PORT}"

    async def authenticate_with_scoped_auth(
        self,
        client: AsyncClient,
        user_openstack_id: str,
        domain_openstack_id: str,
        password: str,
        project_openstack_id: str,
    ) -> tuple[str, str]:
        response: Response = await self.request(
            client=client,
            url=self._KEYSTONE_URL + "/v3/auth/tokens",
            method="POST",
            headers={"Content-Type": "application/json"},
            json={
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "id": user_openstack_id,
                                "domain": {
                                    "id": domain_openstack_id
                                },
                                "password": password,
                            }
                        }
                    },
                    "scope": {
                        "project": {
                            "id": project_openstack_id
                        },
                    },
                },
            },
        )

        keystone_token: str = response.headers.get("x-subject-token")
        keystone_token_expires_at: str = response.json().get("token").get("expires_at")
        return keystone_token, keystone_token_expires_at
