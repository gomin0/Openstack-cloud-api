from httpx import AsyncClient, Response

from common.envs import get_envs
from domain.security_group.entity import SecurityGroupRule
from infrastructure.openstack_client import OpenStackClient

envs = get_envs()


class NeutronClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NEUTRON_PORT: int = envs.NEUTRON_PORT
    _NEUTRON_URL: str = f"{_OPEN_STACK_URL}:{_NEUTRON_PORT}"

    async def get_security_group_rules(
        self,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str | None = None,
        security_group_openstack_id: str | None = None,
    ) -> list[SecurityGroupRule]:
        if project_openstack_id is not None:
            parameter = {"project_id": project_openstack_id}
        elif security_group_openstack_id is not None:
            parameter = {"security_group_id": security_group_openstack_id}
        else:
            parameter = {}
        response: Response = await self.request(
            client=client,
            method="GET",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules",
            headers={"X-Auth-Token": keystone_token},
            params=parameter,
        )
        rules: list[dict] = response.json().get("security_group_rules", [])
        return [SecurityGroupRule.from_dict(rule) for rule in rules]
