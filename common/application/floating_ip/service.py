from fastapi import Depends

from common.application.floating_ip.response import FloatingIpDetailsResponse, FloatingIpDetailResponse, \
    FloatingIpResponse
from common.domain.enum import SortOrder
from common.domain.floating_ip.dto import FloatingIpDTO
from common.domain.floating_ip.entity import FloatingIp
from common.domain.floating_ip.enum import FloatingIpSortOption
from common.exception.floating_ip_exception import FloatingIpNotFoundException, FloatingIpAccessDeniedException
from common.infrastructure.database import transactional
from common.infrastructure.floating_ip.repository import FloatingIpRepository
from common.infrastructure.neutron.client import NeutronClient
from common.util.compensating_transaction import CompensationManager


class FloatingIpService:
    def __init__(
        self,
        floating_ip_repository: FloatingIpRepository = Depends(),
        neutron_client: NeutronClient = Depends(),
    ):
        self.floating_ip_repository = floating_ip_repository
        self.neutron_client = neutron_client

    @transactional
    async def find_floating_ips_details(
        self,
        project_id: int,
        sort_by: FloatingIpSortOption = FloatingIpSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
    ) -> FloatingIpDetailsResponse:
        floating_ips: list[FloatingIp] = await self.floating_ip_repository.find_all_by_project_id(
            project_id=project_id,
            sort_by=sort_by,
            order=order,
            with_deleted=with_deleted,
            with_relations=True
        )

        return FloatingIpDetailsResponse(
            floating_ips=[await FloatingIpDetailResponse.from_entity(floating_ip) for floating_ip in floating_ips]
        )

    @transactional
    async def get_floating_ip_detail(
        self,
        project_id: int,
        floating_ip_id: int,
        with_deleted: bool = False,
    ) -> FloatingIpDetailResponse:
        floating_ip: FloatingIp | None = await self.floating_ip_repository.find_by_id(
            floating_ip_id=floating_ip_id,
            with_deleted=with_deleted,
            with_relations=True
        )
        if not floating_ip:
            raise FloatingIpNotFoundException()

        if project_id != floating_ip.project_id:
            raise FloatingIpAccessDeniedException()

        return await FloatingIpDetailResponse.from_entity(floating_ip)

    @transactional
    async def create_floating_ip(
        self,
        compensating_tx: CompensationManager,
        project_id: int,
        keystone_token: str,
        floating_network_id: str,
    ) -> FloatingIpResponse:
        floating_ip_info: FloatingIpDTO = await self.neutron_client.create_floating_ip(
            floating_network_id=floating_network_id,
            keystone_token=keystone_token,
        )
        floating_ip_openstack_id: str = floating_ip_info.openstack_id
        floating_ip_address: str = floating_ip_info.address

        compensating_tx.add_task(
            lambda: self.neutron_client.delete_floating_ip(
                floating_ip_openstack_id=floating_ip_openstack_id,
                keystone_token=keystone_token,
            )
        )

        floating_ip: FloatingIp = FloatingIp.create(
            openstack_id=floating_ip_openstack_id,
            project_id=project_id,
            address=floating_ip_address,
        )
        floating_ip: FloatingIp = await self.floating_ip_repository.create(floating_ip=floating_ip)

        return FloatingIpResponse.from_entity(floating_ip)

    @transactional
    async def delete_floating_ip(
        self,
        project_id: int,
        keystone_token: str,
        floating_ip_id: int
    ) -> None:

        floating_ip: FloatingIp | None = await self.floating_ip_repository.find_by_id(floating_ip_id=floating_ip_id)
        if not floating_ip:
            raise FloatingIpNotFoundException()

        floating_ip.validate_delete_permission(project_id=project_id)
        floating_ip.validate_deletable()
        floating_ip.delete()

        await self.neutron_client.delete_floating_ip(
            keystone_token=keystone_token,
            floating_ip_openstack_id=floating_ip.openstack_id
        )
