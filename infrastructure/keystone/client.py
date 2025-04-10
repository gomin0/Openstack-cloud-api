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
        """
        :return: 생성된 subject token과 token의 만료 시각이 담긴 tuple
        """
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

    async def authenticate_with_unscoped_auth(
        self,
        client: AsyncClient,
        user_openstack_id: str,
        domain_openstack_id: str,
        password: str,
    ) -> tuple[str, str]:
        """
        :return: 생성된 subject token과 token의 만료 시각이 담긴 tuple
        """
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
                                    "id": domain_openstack_id,
                                },
                                "password": password,
                            }
                        }
                    },
                },
            },
        )

        keystone_token: str = response.headers.get("x-subject-token")
        keystone_token_expires_at: str = response.json().get("token").get("expires_at")
        return keystone_token, keystone_token_expires_at

    async def create_user(
        self,
        client: AsyncClient,
        keystone_token: str,
        domain_openstack_id: str,
        account_id: str,
        password: str,
    ) -> str:
        """
        :return: 생성된 유저의 openstack id
        """
        response: Response = await self.request(
            client=client,
            method="POST",
            url=self._KEYSTONE_URL + "/v3/users",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "user": {
                    "domain_id": domain_openstack_id,
                    "name": account_id,
                    "password": password,
                }
            }
        )
        return response.json().get("user").get("id")

    async def delete_user(
        self,
        client: AsyncClient,
        keystone_token: str,
        user_openstack_id: str,
    ) -> None:
        await self.request(
            client=client,
            method="DELETE",
            url=self._KEYSTONE_URL + f"/v3/users/{user_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
