import uuid

from httpx import AsyncClient, Response

from common.domain.server.dto import OsServerDto
from common.domain.server.enum import ServerStatus
from common.exception.openstack_exception import OpenStackException
from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()


class NovaClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NOVA_PORT: int = envs.NOVA_PORT
    _NOVA_URL: str = f"{_OPEN_STACK_URL}:{_NOVA_PORT}"

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

    async def get_vnc_console(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str
    ) -> str:
        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NOVA_URL}/v2.1/servers/{server_openstack_id}/action",
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

    async def exists_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
    ) -> bool:
        try:
            await self.request(
                client=client,
                method="GET",
                url=f"{self._NOVA_URL}/v2.1/servers/{server_openstack_id}",
                headers={"X-Auth-Token": keystone_token},
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 404:
                return False
            raise ex

        return True

    async def create_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        flavor_openstack_id: str,
        image_openstack_id: str,
        network_interface_openstack_id: str,
        root_volume_size: int,
    ) -> str:
        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NOVA_URL}/v2.1/servers",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "server": {
                    "name": f"server_{uuid.uuid4()}",
                    "flavorRef": flavor_openstack_id,
                    "networks": [{"port": network_interface_openstack_id}],
                    "block_device_mapping_v2": [
                        {
                            "uuid": image_openstack_id,
                            "source_type": "image",
                            "destination_type": "volume",
                            "delete_on_termination": True,
                            "boot_index": 0,
                            "volume_size": root_volume_size,
                        },
                    ],
                },
            },
        )
        return response.json().get("server", {}).get("id")

    async def delete_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
    ) -> None:
        await self.request(
            client=client,
            method="DELETE",
            url=f"{self._NOVA_URL}/v2.1/servers/{server_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )

    async def attach_volume_to_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
        volume_openstack_id: str,
    ) -> None:
        await self.request(
            client=client,
            method="POST",
            url=self._NOVA_URL + f"/v2.1/servers/{server_openstack_id}/os-volume_attachments",
            headers={
                "Content-Type": "application/json",
                "X-Auth-Token": keystone_token,
            },
            json={
                "volumeAttachment": {
                    "volumeId": volume_openstack_id,
                },
            },
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

    async def detach_volume_from_server(
        self,
        client: AsyncClient,
        keystone_token: str,
        server_openstack_id: str,
        volume_openstack_id: str
    ) -> None:
        await self.request(
            client=client,
            method="DELETE",
            url=self._NOVA_URL + f"/v2.1/servers/{server_openstack_id}/os-volume_attachments/{volume_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
