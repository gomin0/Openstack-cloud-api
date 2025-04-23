from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from domain.enum import SortOrder
from domain.security_group.entity import SecurityGroup, SecurityGroupRule
from domain.security_group.enum import SecurityGroupSortOption
from exception.security_group_exception import SecurityGroupNotFoundException, SecurityGroupAccessDeniedException
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

    @transactional()
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
        security_groups: list[SecurityGroup] = await self.security_group_repository.find_all_by_project_id(
            session=session,
            project_id=project_id,
            sort_by=sort_by,
            order=sort_order,
            with_deleted=with_deleted,
        )

        rules: list[SecurityGroupRule] = await self.neutron_client.get_security_group_rules(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=project_openstack_id,
        )

        response_items: list[SecurityGroupDetailResponse] = [
            await SecurityGroupDetailResponse.from_entity(
                security_group,
                [rule for rule in rules if rule.security_group_openstack_id == security_group.openstack_id]
            )
            for security_group in security_groups
        ]

        return SecurityGroupDetailsResponse(security_groups=response_items)

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
