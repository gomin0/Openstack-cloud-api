from httpx import AsyncClient, Response

from common.domain.floating_ip.dto import FloatingIpDTO
from common.domain.security_group.dto import SecurityGroupRuleDTO, SecurityGroupDTO, CreateSecurityGroupRuleDTO
from common.domain.security_group.enum import SecurityGroupRuleDirection
from common.infrastructure.openstack_client import OpenStackClient
from common.util.envs import get_envs

envs = get_envs()


class NeutronClient(OpenStackClient):
    _OPEN_STACK_URL: str = envs.OPENSTACK_SERVER_URL
    _NEUTRON_PORT: int = envs.NEUTRON_PORT
    _NEUTRON_URL: str = f"{_OPEN_STACK_URL}:{_NEUTRON_PORT}"

    async def find_security_group_rules(
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
                ether_type=rule.get("ethertype"),
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
                ether_type=rule.get("ethertype"),
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
        security_group_rules: list[CreateSecurityGroupRuleDTO]
    ) -> list[SecurityGroupRuleDTO]:

        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules",
            headers={"X-Auth-Token": keystone_token},
            json={
                "security_group_rules": [
                    {
                        "protocol": rule.protocol,
                        "direction": rule.direction.value,
                        "ethertype": rule.ether_type.value,
                        "port_range_min": rule.port_range_min,
                        "port_range_max": rule.port_range_max,
                        "remote_ip_prefix": rule.remote_ip_prefix,
                        "security_group_id": security_group_openstack_id,
                    }
                    for rule in security_group_rules
                ]
            }
        )
        created_rules_data = response.json().get("security_group_rules", [])

        security_group_rules: list[SecurityGroupRuleDTO] = [
            SecurityGroupRuleDTO(
                openstack_id=rule_data["id"],
                security_group_openstack_id=rule_data["security_group_id"],
                protocol=rule_data["protocol"],
                ether_type=rule_data["ethertype"],
                direction=rule_data["direction"],
                port_range_min=rule_data["port_range_min"],
                port_range_max=rule_data["port_range_max"],
                remote_ip_prefix=rule_data["remote_ip_prefix"],
            )
            for rule_data in created_rules_data
        ]

        return security_group_rules

    async def create_floating_ip(
        self,
        client: AsyncClient,
        keystone_token: str,
        floating_network_id: str,
    ) -> FloatingIpDTO:
        response: Response = await self.request(
            client=client,
            method="POST",
            url=f"{self._NEUTRON_URL}/v2.0/floatingips",
            headers={"X-Auth-Token": keystone_token},
            json={"floatingip": {"floating_network_id": floating_network_id}}
        )
        data = response.json()["floatingip"]

        return FloatingIpDTO(
            openstack_id=data["id"],
            status=data["status"],
            address=data["floating_ip_address"],
        )

    async def update_security_group(
        self,
        client: AsyncClient,
        keystone_token: str,
        security_group_openstack_id: str,
        name: str,
    ) -> None:
        await self.request(
            client=client,
            method="PUT",
            url=f"{self._NEUTRON_URL}/v2.0/security-groups/{security_group_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
            json={
                "security_group": {
                    "name": name
                }
            },
        )

    async def attach_floating_ip_to_network_interface(
        self,
        client: AsyncClient,
        keystone_token: str,
        floating_ip_openstack_id: str,
        network_interface_id: str
    ) -> None:
        await self.request(
            client=client,
            method="PUT",
            url=f"{self._NEUTRON_URL}/v2.0/floatingips/{floating_ip_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
            json={
                "floatingip": {
                    "port_id": network_interface_id
                }
            }
        )

    async def detach_floating_ip_from_network_interface(
        self,
        client: AsyncClient,
        keystone_token: str,
        floating_ip_openstack_id: str,
    ) -> None:
        await self.request(
            client=client,
            method="PUT",
            url=f"{self._NEUTRON_URL}/v2.0/floatingips/{floating_ip_openstack_id}",
            headers={"X-Auth-Token": keystone_token},
            json={
                "floatingip": {
                    "port_id": None
                }
            }
        )

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

    async def delete_security_group_rule(
        self,
        client: AsyncClient,
        keystone_token: str,
        security_group_rule_openstack_id: str,
    ) -> None:
        await self.request(
            client=client,
            method="DELETE",
            url=f"{self._NEUTRON_URL}/v2.0/security-group-rules/{security_group_rule_openstack_id}",
            headers={"X-Auth-Token": keystone_token}
        )

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
