from httpx import AsyncClient, Response

from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import get_envs

envs = get_envs()


class NeutronClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NEUTRON_PORT: int = envs.NEUTRON_PORT
    _NEUTRON_URL: str = f"{_OPEN_STACK_URL}:{_NEUTRON_PORT}"

    async def create_floating_ip(
        self,
        client: AsyncClient,
        keystone_token: str,
        floating_network_id: str,
    ) -> tuple[str, str]:
        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NEUTRON_URL}/v2.0/floatingips",
            headers={"X-Auth-Token": keystone_token},
            json={"floatingip": {"floating_network_id": floating_network_id}}
        )
        data = response.json()["floatingip"]

        return data["id"], data["floating_ip_address"]

    async def delete_floating_ip(
        self,
        client: AsyncClient,
        keystone_token: str,
        floating_ip_openstack_id: str,
    ) -> None:
        await self.request(
            client=client,
            method="DELETE",
            url=f"{self._NEUTRON_URL}/v2.0/floatingips/{floating_ip_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
        )
