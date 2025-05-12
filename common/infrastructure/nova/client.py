from httpx import AsyncClient

from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()


class NovaClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NOVA_PORT: int = envs.NOVA_PORT
    _NOVA_URL: str = f"{_OPEN_STACK_URL}:{_NOVA_PORT}"

    async def create_console(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str
    ) -> str:
        response = await self.request(
            client=client,
            method="POST",
            url=self._NOVA_URL + f"/v2/servers/{server_openstack_id}/action",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "os-getVNCConsole": {
                    "type": "novnc"
                }
            }
        )
        return response.json().get("console").get("url")
