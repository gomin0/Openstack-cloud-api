from collections import defaultdict

from httpx import AsyncClient, Response

from application.security_group.dto import SecurityGroupRuleDTO
from common.envs import get_envs
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
        filter_by: dict
    ) -> dict[str, list[SecurityGroupRuleDTO]]:
        response: Response = await self.request(
            client=client,
            method="GET",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules",
            headers={"X-Auth-Token": keystone_token},
            params=filter_by,
        )
        rules: list[dict] = response.json().get("security_group_rules", [])
        grouped: dict[str, list[SecurityGroupRuleDTO]] = defaultdict(list)
        for rule in rules:
            security_group_openstack_id = rule["security_group_id"]
            dto = SecurityGroupRuleDTO.from_dict(rule)
            grouped[security_group_openstack_id].append(dto)

        return grouped
