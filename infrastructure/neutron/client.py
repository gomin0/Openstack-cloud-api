from httpx import AsyncClient, Response

from common.envs import get_envs
from infrastructure.openstack_client import OpenStackClient

envs = get_envs()


class NeutronClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NEUTRON_PORT: int = envs.NEUTRON_PORT
    _NEUTRON_URL: str = f"{_OPEN_STACK_URL}:{_NEUTRON_PORT}"

    async def get_security_group_rules_in_project(
        self,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
    ) -> list[dict]:
        response: Response = await self.request(
            client=client,
            method="GET",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules?project_id={project_openstack_id}",
            headers={"X-Auth-Token": keystone_token}
        )
        return response.json().get("security_group_rules", [])

    async def get_security_group_rules_in_security_group(
        self,
        client: AsyncClient,
        keystone_token: str,
        security_group_openstack_id: str
    ) -> list[dict]:
        response: Response = await self.request(
            client=client,
            method="GET",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules?security_group_id={security_group_openstack_id}",
            headers={"X-Auth-Token": keystone_token}
        )
        return response.json().get("security_group_rules", [])

    async def create_security_group(
        self,
        client: AsyncClient,
        keystone_token: str,
        name: str,
        description: str
    ) -> dict:
        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NEUTRON_URL}/v2.0/security-groups",
            headers={"X-Auth-Token": keystone_token},
            json={
                "security_group": {
                    "name": name,
                    "description": description
                }
            }
        )
        return response.json()["security_group"]

    async def delete_security_group(
        self,
        client: AsyncClient,
        keystone_token: str,
        security_group_openstack_id: str
    ) -> None:
        await self.request(
            client=client,
            method="DELETE",
            url=f"{self._NEUTRON_URL}/v2.0/security-groups/{security_group_openstack_id}",
            headers={"X-Auth-Token": keystone_token}
        )

    async def create_security_group_rules(
        self,
        client: AsyncClient,
        keystone_token: str,
        security_group_rules: list[dict]
    ) -> None:
        await self.request(
            client=client,
            method="POST",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules",
            headers={"X-Auth-Token": keystone_token},
            json={"security_group_rules": security_group_rules}
        )
