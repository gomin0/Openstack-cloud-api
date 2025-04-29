from httpx import AsyncClient, Response

from common.domain.security_group.dto import SecurityGroupRuleDTO, SecurityGroupDTO, CreateSecurityGroupRuleDTO
from common.domain.security_group.enum import SecurityGroupRuleDirection
from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import get_envs

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
    ) -> list[SecurityGroupRuleDTO]:
        parameter: dict[str, str] = {}
        if project_openstack_id is not None:
            parameter["project_id"] = project_openstack_id
        if security_group_openstack_id is not None:
            parameter["security_group_id"] = security_group_openstack_id

        response: Response = await self.request(
            client=client,
            method="GET",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules",
            headers={"X-Auth-Token": keystone_token},
            params=parameter,
        )
        rules: list[dict] = response.json().get("security_group_rules", [])

        return [
            SecurityGroupRuleDTO(
                openstack_id=rule["id"],
                security_group_openstack_id=rule["security_group_id"],
                protocol=rule.get("protocol"),
                direction=SecurityGroupRuleDirection(rule["direction"]),
                port_range_min=rule.get("port_range_min"),
                port_range_max=rule.get("port_range_max"),
                remote_ip_prefix=rule.get("remote_ip_prefix"),
            )
            for rule in rules
        ]

    async def create_security_group(
        self,
        client: AsyncClient,
        keystone_token: str,
        name: str,
        description: str
    ) -> SecurityGroupDTO:
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

        security_group = response.json()["security_group"]

        default_rules = security_group.get("security_group_rules", [])

        rules: list[SecurityGroupRuleDTO] = [
            SecurityGroupRuleDTO(
                openstack_id=security_group["id"],
                security_group_openstack_id=security_group["id"],
                protocol=rule.get("protocol"),
                direction=SecurityGroupRuleDirection(rule["direction"]),
                port_range_min=rule.get("port_range_min"),
                port_range_max=rule.get("port_range_max"),
                remote_ip_prefix=rule.get("remote_ip_prefix"),
            )
            for rule in default_rules
        ]
        return SecurityGroupDTO(
            openstack_id=security_group["id"],
            rules=rules,
            name=security_group["name"],
            description=security_group["description"],
        )

    async def create_security_group_rules(
        self,
        client: AsyncClient,
        keystone_token: str,
        security_group_openstack_id: str,
        new_rules: list[CreateSecurityGroupRuleDTO]
    ) -> list[SecurityGroupRuleDTO]:
        rules = {
            "security_group_rules": [
                {
                    "protocol": rule.protocol,
                    "direction": rule.direction.value,
                    "port_range_min": rule.port_range_min,
                    "port_range_max": rule.port_range_max,
                    "remote_ip_prefix": rule.remote_ip_prefix,
                    "security_group_id": security_group_openstack_id,
                }
                for rule in new_rules
            ]
        }

        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules",
            headers={"X-Auth-Token": keystone_token},
            json=rules
        )
        created_rules_data = response.json().get("security_group_rules", [])

        security_group_rules: list[SecurityGroupRuleDTO] = [
            SecurityGroupRuleDTO(
                openstack_id=rule_data["id"],
                security_group_openstack_id=rule_data["security_group_id"],
                protocol=rule_data["protocol"],
                direction=rule_data["direction"],
                port_range_min=rule_data["port_range_min"],
                port_range_max=rule_data["port_range_max"],
                remote_ip_prefix=rule_data["remote_ip_prefix"],
            )
            for rule_data in created_rules_data
        ]

        return security_group_rules

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
