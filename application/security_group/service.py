from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.security_group.response import SecurityGroupDetailsResponse, SecurityGroupDetailResponse
from domain.enum import SortOrder
from domain.project.entity import Project
from domain.security_group.entity import SecurityGroup
from domain.security_group.enum import SecurityGroupSortOption
from exception.project_exception import ProjectNotFoundException
from infrastructure.database import transactional
from infrastructure.neutron.client import NeutronClient
from infrastructure.project.repository import ProjectRepository
from infrastructure.security_group.repository import SecurityGroupRepository


class SecurityGroupService:
    def __init__(
        self,
        security_group_repository: SecurityGroupRepository = Depends(),
        project_repository: ProjectRepository = Depends(),
        neutron_client: NeutronClient = Depends(),
    ):
        self.security_group_repository = security_group_repository
        self.project_repository = project_repository
        self.neutron_client = neutron_client

    @transactional()
    async def find_security_groups_details(
        self,
        session: AsyncSession,
        client: AsyncClient,
        project_id: int,
        keystone_token: str,
        sort_by: SecurityGroupSortOption = SecurityGroupSortOption.CREATED_AT,
        sort_order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> SecurityGroupDetailsResponse:
        project: Project | None = await self.project_repository.find_by_id(
            session=session,
            project_id=project_id
        )
        if not project:
            raise ProjectNotFoundException()

        security_groups: list[SecurityGroup] | None = await self.security_group_repository.find_by_project_id(
            session=session,
            project_id=project_id,
            sort_by=sort_by,
            order=sort_order,
            with_deleted=with_deleted,
            with_relations=with_relations,
        )

        rules: list[dict] = await self.neutron_client.get_security_group_rules_in_project(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=project.openstack_id,
        )

        rule_map: dict[str, list[dict]] = {}
        for rule in rules:
            security_group_openstack_id = rule.get("security_group_id")
            rule_map.setdefault(security_group_openstack_id, []).append(rule)

        response_items: list[SecurityGroupDetailResponse] = [
            await SecurityGroupDetailResponse.from_entity(security_group, rule_map.get(security_group.openstack_id, []))
            for security_group in security_groups
        ]

        return SecurityGroupDetailsResponse(security_groups=response_items)
