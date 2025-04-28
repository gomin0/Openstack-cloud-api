from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.security_group.dto import SecurityGroupRuleDTO
from application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from common.compensating_transaction import CompensationManager
from domain.enum import SortOrder
from domain.security_group.entity import SecurityGroup, SecurityGroupRule
from domain.security_group.enum import SecurityGroupSortOption
from exception.openstack_exception import OpenStackException
from exception.security_group_exception import SecurityGroupAccessDeniedException, SecurityGroupRuleDuplicatedException
from exception.security_group_exception import SecurityGroupNotFoundException, SecurityGroupNameDuplicatedException
from infrastructure.database import transactional
from infrastructure.neutron.client import NeutronClient
from infrastructure.security_group.repository import SecurityGroupRepository


class SecurityGroupService:
    def __init__(
        self,
        security_group_repository: SecurityGroupRepository = Depends(),
        neutron_client: NeutronClient = Depends(),
    ):
        self.security_group_repository = security_group_repository
        self.neutron_client = neutron_client

    async def find_security_groups_details(
        self,
        session: AsyncSession,
        client: AsyncClient,
        project_id: int,
        project_openstack_id: str,
        keystone_token: str,
        sort_by: SecurityGroupSortOption = SecurityGroupSortOption.CREATED_AT,
        sort_order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
    ) -> SecurityGroupDetailsResponse:
        security_groups: list[SecurityGroup] = await self._find_security_groups_by_project_id(
            session=session,
            project_id=project_id,
            sort_by=sort_by,
            sort_order=sort_order,
            with_deleted=with_deleted,
        )
        rules: list[SecurityGroupRule] = await self.neutron_client.get_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=project_openstack_id,
        )

        rule_map: dict[str, list[SecurityGroupRule]] = defaultdict(list)
        for rule in rules:
            rule_map[rule.security_group_openstack_id].append(rule)

        response_items: list[SecurityGroupDetailResponse] = [
            await SecurityGroupDetailResponse.from_entity(
                security_group,
                rule_map.get(security_group.openstack_id, [])
            )
            for security_group in security_groups
        ]

        return SecurityGroupDetailsResponse(security_groups=response_items)

    @transactional()
    async def _find_security_groups_by_project_id(
        self,
        session: AsyncSession,
        project_id: int,
        sort_by: SecurityGroupSortOption,
        sort_order: SortOrder,
        with_deleted: bool
    ) -> list[SecurityGroup]:
        security_groups: list[SecurityGroup] = await self.security_group_repository.find_all_by_project_id(
            session=session,
            project_id=project_id,
            sort_by=sort_by,
            order=sort_order,
            with_deleted=with_deleted,
            with_relations=True,
        )

        return security_groups

    @transactional()
    async def get_security_group_detail(
        self,
        session: AsyncSession,
        client: AsyncClient,
        project_id: int,
        keystone_token: str,
        security_group_id: int,
        with_deleted: bool = False,
    ) -> SecurityGroupDetailResponse:
        security_group: SecurityGroup | None = await self.security_group_repository.find_by_id(
            session=session,
            security_group_id=security_group_id,
            with_deleted=with_deleted,
            with_relations=True
        )
        if not security_group:
            raise SecurityGroupNotFoundException()

        if project_id != security_group.project_id:
            raise SecurityGroupAccessDeniedException()

        rules: list[SecurityGroupRule] = await self.neutron_client.get_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            security_group_openstack_id=security_group.openstack_id,
        )
        return await SecurityGroupDetailResponse.from_entity(security_group, rules)

    @transactional()
    async def create_security_group(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        name: str,
        description: str | None,
        rules: list[SecurityGroupRuleDTO]
    ) -> SecurityGroupDetailResponse:
        if await self.security_group_repository.exists_by_project_and_name(
            session=session,
            project_id=project_id,
            name=name
        ):
            raise SecurityGroupNameDuplicatedException()

        try:
            security_group_openstack_id: str = await self.neutron_client.create_security_group(
                client=client,
                keystone_token=keystone_token,
                name=name,
                description=description
            )

            compensating_tx.add_task(
                lambda: self.neutron_client.delete_security_group(
                    client=client,
                    keystone_token=keystone_token,
                    security_group_openstack_id=security_group_openstack_id
                )
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 409:
                raise SecurityGroupNameDuplicatedException()
            raise ex

        security_group: SecurityGroup = SecurityGroup.create(
            openstack_id=security_group_openstack_id,
            project_id=project_id,
            name=name,
            description=description,
        )

        security_group: SecurityGroup = await self.security_group_repository.create(
            session=session,
            security_group=security_group
        )

        if rules:
            try:
                security_group_rules: list[SecurityGroupRule] = [
                    SecurityGroupRule(
                        id="",
                        security_group_openstack_id=security_group_openstack_id,
                        protocol=rule.protocol,
                        direction=rule.direction,
                        port_range_min=rule.port_range_min,
                        port_range_max=rule.port_range_max,
                        remote_ip_prefix=rule.remote_ip_prefix,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    for rule in rules
                ]

                await self.neutron_client.create_security_group_rules(
                    client=client,
                    keystone_token=keystone_token,
                    security_group_rules=security_group_rules
                )
            except OpenStackException as ex:
                if ex.openstack_status_code == 404:
                    raise SecurityGroupNotFoundException()
                if ex.openstack_status_code == 409:
                    raise SecurityGroupRuleDuplicatedException()
                raise ex

        # 생성 된 룰 조회(생성한 룰셋 + default rule)
        security_group_rules = await self.neutron_client.get_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            security_group_openstack_id=security_group_openstack_id
        )

        return await SecurityGroupDetailResponse.from_entity(security_group, security_group_rules)
