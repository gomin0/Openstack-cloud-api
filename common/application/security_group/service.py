import asyncio
from collections import defaultdict

import backoff
from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from common.application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from common.domain.enum import SortOrder
from common.domain.security_group.dto import CreateSecurityGroupRuleDTO, SecurityGroupRuleDTO, SecurityGroupDTO, \
    UpdateSecurityGroupRuleDTO
from common.domain.security_group.entity import SecurityGroup
from common.domain.security_group.enum import SecurityGroupSortOption
from common.exception.security_group_exception import (
    SecurityGroupNotFoundException,
    SecurityGroupAccessDeniedException,
    SecurityGroupNameDuplicatedException,
    SecurityGroupUpdatePermissionDeniedException
)
from common.infrastructure.database import transactional
from common.infrastructure.neutron.client import NeutronClient
from common.infrastructure.security_group.repository import SecurityGroupRepository
from common.util.compensating_transaction import CompensationManager


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
        rules: list[SecurityGroupRuleDTO] = await self.neutron_client.find_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=project_openstack_id,
        )

        rule_map: dict[str, list[SecurityGroupRuleDTO]] = defaultdict(list)
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

        rules: list[SecurityGroupRuleDTO] = await self.neutron_client.find_security_group_rules(
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
        rules: list[CreateSecurityGroupRuleDTO]
    ) -> SecurityGroupDetailResponse:
        if await self.security_group_repository.exists_by_project_and_name(
            session=session,
            project_id=project_id,
            name=name
        ):
            raise SecurityGroupNameDuplicatedException()

        # (OpenStack) 보안 그룹 생성
        openstack_security_group: SecurityGroupDTO = await self.neutron_client.create_security_group(
            client=client,
            keystone_token=keystone_token,
            name=name,
            description=description
        )
        compensating_tx.add_task(
            lambda: self.neutron_client.delete_security_group(
                client=client,
                keystone_token=keystone_token,
                security_group_openstack_id=openstack_security_group.openstack_id
            )
        )

        # (DB) 보안 그룹 생성
        security_group: SecurityGroup = SecurityGroup.create(
            openstack_id=openstack_security_group.openstack_id,
            project_id=project_id,
            name=name,
            description=description,
        )
        security_group: SecurityGroup = await self.security_group_repository.create(
            session=session,
            security_group=security_group
        )

        # 보안 그룹 rule 생성(default rule 과 다른 룰만)
        if not rules:
            return await SecurityGroupDetailResponse.from_entity(security_group, openstack_security_group.rules)

        security_group_rules: list[SecurityGroupRuleDTO] = []
        default_rule_keys: set[tuple] = {
            (r.protocol, r.direction, r.port_range_min, r.port_range_max, r.remote_ip_prefix)
            for r in openstack_security_group.rules
        }
        new_rules: list[CreateSecurityGroupRuleDTO] = [
            r for r in rules
            if (r.protocol, r.direction, r.port_range_min, r.port_range_max, r.remote_ip_prefix)
               not in default_rule_keys
        ]
        if new_rules:
            security_group_rules: list[SecurityGroupRuleDTO] = await self.neutron_client.create_security_group_rules(
                client=client,
                keystone_token=keystone_token,
                security_group_rules=new_rules,
                security_group_openstack_id=security_group.openstack_id,
            )

        security_group_rules += openstack_security_group.rules
        return await SecurityGroupDetailResponse.from_entity(security_group, security_group_rules)

    @backoff.on_exception(backoff.expo, StaleDataError, max_tries=3)
    @transactional()
    async def update_security_group_detail(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        security_group_id: int,
        name: str,
        description: str | None,
        rules: list[UpdateSecurityGroupRuleDTO]
    ) -> SecurityGroupDetailResponse:
        security_group: SecurityGroup | None = await self.security_group_repository.find_by_id(
            session=session,
            security_group_id=security_group_id,
        )
        if not security_group:
            raise SecurityGroupNotFoundException()

        if not security_group.is_owned_by(project_id):
            raise SecurityGroupUpdatePermissionDeniedException()

        if security_group.name != name and await self.security_group_repository.exists_by_project_and_name(
            session=session,
            project_id=project_id,
            name=name
        ):
            raise SecurityGroupNameDuplicatedException()

        existing_name: str = security_group.name

        security_group.update_info(name=name, description=description)
        security_group: SecurityGroup = await self.security_group_repository.update_with_optimistic_lock(
            session=session,
            security_group=security_group
        )

        # 기존 보안 그룹 룰셋 조회
        existing_rules: list[SecurityGroupRuleDTO] = await self.neutron_client.find_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            security_group_openstack_id=security_group.openstack_id,
        )

        # 삭제할 룰셋 / 추가할 룰셋 구분
        rules_to_delete: list[SecurityGroupRuleDTO] = []
        rules_to_keep: list[SecurityGroupRuleDTO] = []
        for rule in existing_rules:
            if rule.to_dto() not in rules:
                rules_to_delete.append(rule)
                continue
            rules_to_keep.append(rule)

        existing_rules_to_compare: list[UpdateSecurityGroupRuleDTO] = [
            existing_rule.to_update_dto() for existing_rule in existing_rules
        ]
        rules_to_add: list[UpdateSecurityGroupRuleDTO] = [
            rule for rule in rules
            if rule not in existing_rules_to_compare
        ]

        security_group_openstack_id: str = security_group.openstack_id

        # openstack security group update API 호출 (name 이 변경된 경우 에만 호출)
        if name != existing_name:
            await self.neutron_client.update_security_group(
                client=client,
                keystone_token=keystone_token,
                security_group_openstack_id=security_group_openstack_id,
                name=name
            )
            compensating_tx.add_task(
                lambda: self.neutron_client.update_security_group(
                    client=client,
                    keystone_token=keystone_token,
                    security_group_openstack_id=security_group_openstack_id,
                    name=existing_name
                )
            )

        # rule 에 변경 사항이 없는 경우
        if not rules_to_delete and not rules_to_add:
            return await SecurityGroupDetailResponse.from_entity(security_group, existing_rules)

        # 삭제 해야 할 룰 삭제
        if rules_to_delete:
            await self._delete_security_group_rules(
                client=client,
                keystone_token=keystone_token,
                rules_to_delete=rules_to_delete,
                security_group_openstack_id=security_group_openstack_id,
                compensating_tx=compensating_tx
            )
        # 추가할 새로운 룰셋 생성
        created_rules: list[SecurityGroupRuleDTO] = []
        if rules_to_add:
            new_rules = [rule.to_create_dto() for rule in rules_to_add]
            created_rules = await self._create_security_group_rules(
                client=client,
                keystone_token=keystone_token,
                rules_to_add=new_rules,
                security_group_openstack_id=security_group_openstack_id,
                compensating_tx=compensating_tx
            )

        return await SecurityGroupDetailResponse.from_entity(security_group, rules_to_keep + created_rules)

    async def _delete_security_group_rules(
        self,
        compensating_tx: CompensationManager,
        client: AsyncClient,
        security_group_openstack_id: str,
        keystone_token: str,
        rules_to_delete: list[SecurityGroupRuleDTO],
    ) -> None:
        tasks = []

        for rule in rules_to_delete:
            delete_task = self.neutron_client.delete_security_group_rule(
                client=client,
                keystone_token=keystone_token,
                security_group_rule_openstack_id=rule.openstack_id
            )
            compensating_tx.add_task(
                lambda: self.neutron_client.create_security_group_rules(
                    client=client,
                    keystone_token=keystone_token,
                    security_group_openstack_id=security_group_openstack_id,
                    security_group_rules=[CreateSecurityGroupRuleDTO(
                        protocol=rule.protocol,
                        direction=rule.direction,
                        port_range_min=rule.port_range_min,
                        port_range_max=rule.port_range_max,
                        remote_ip_prefix=rule.remote_ip_prefix
                    )],
                )
            )
            tasks.append(delete_task)

        await asyncio.gather(*tasks)

    async def _create_security_group_rules(
        self,
        compensating_tx: CompensationManager,
        client: AsyncClient,
        security_group_openstack_id: str,
        keystone_token: str,
        rules_to_add: list[CreateSecurityGroupRuleDTO],
    ) -> list[SecurityGroupRuleDTO]:
        created_rules: list[SecurityGroupRuleDTO] = await self.neutron_client.create_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            security_group_openstack_id=security_group_openstack_id,
            security_group_rules=rules_to_add
        )
        for rule in created_rules:
            compensating_tx.add_task(
                lambda: self.neutron_client.delete_security_group_rule(
                    client=client,
                    keystone_token=keystone_token,
                    security_group_rule_openstack_id=rule.openstack_id
                )
            )
        return created_rules
