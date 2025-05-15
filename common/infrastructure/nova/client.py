from httpx import AsyncClient, Response

from common.domain.server.dto import OsServerDto
from common.domain.server.enum import ServerStatus
from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()


class NovaClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NOVA_PORT: int = envs.NOVA_PORT
    _NOVA_URL: str = f"{_OPEN_STACK_URL}:{_NOVA_PORT}"

    async def get_vnc_console(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str
    ) -> str:
        response: Response = await self.request(
            client=client,
            method="POST",
            url=self._NOVA_URL + f"/v2.1/servers/{server_openstack_id}/action",
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

    async def get_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
    ) -> OsServerDto:
        response: Response = await self.request(
            client=client,
            method="GET",
            url=f"{self._NOVA_URL}/v2.1/servers/{server_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
        server: dict = response.json().get("server", {})
        return OsServerDto(
            openstack_id=server.get("id"),
            project_openstack_id=server.get("tenant_id"),
            status=ServerStatus.parse(server.get("status")),
            volume_openstack_ids=[
                volume_dict.get("id")
                for volume_dict in server.get("os-extended-volumes:volumes_attached")
            ],
        )

    async def start_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str
    ) -> None:
        await self.request(
            client=client,
            method="POST",
            url=self._NOVA_URL + f"/v2.1/servers/{server_openstack_id}/action",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "os-start": None
            }
        )

    async def stop_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str
    ) -> None:
        await self.request(
            client=client,
            method="POST",
            url=self._NOVA_URL + f"/v2.1/servers/{server_openstack_id}/action",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "os-stop": None
            }
        )
