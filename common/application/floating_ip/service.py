from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.floating_ip.response import FloatingIpResponse
from common.domain.floating_ip.entity import FloatingIp
from common.domain.floating_ip.enum import FloatingIpStatus
from common.exception.floating_ip_exception import FloatingNetworkNotFound
from common.exception.openstack_exception import OpenStackException
from common.infrastructure.database import transactional
from common.util.compensating_transaction import CompensationManager
from infrastructure.floating_ip.repository import FloatingIpRepository
from infrastructure.neutron.client import NeutronClient


class FloatingIpService:
    def __init__(
        self,
        floating_ip_repository: FloatingIpRepository = Depends(),
        neutron_client: NeutronClient = Depends(),
    ):
        self.floating_ip_repository = floating_ip_repository
        self.neutron_client = neutron_client

    @transactional()
    async def create_floating_ip(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        project_id: int,
        keystone_token: str,
        floating_network_id: str,
    ) -> FloatingIpResponse:
        try:
            floating_ip_info: tuple[str, str] = await self.neutron_client.create_floating_ip(
                client=client,
                floating_network_id=floating_network_id,
                keystone_token=keystone_token,
            )
            floating_id_openstack_id: str = floating_ip_info[0]
            floating_ip_address: str = floating_ip_info[1]

            compensating_tx.add_task(
                lambda: self.neutron_client.delete_floating_ip(
                    client=client,
                    floating_ip_openstack_id=floating_id_openstack_id,
                    keystone_token=keystone_token,
                )
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 404:
                raise FloatingNetworkNotFound() from ex
            raise ex

        floating_ip: FloatingIp = FloatingIp.create(
            openstack_id=floating_id_openstack_id,
            project_id=project_id,
            server_id=None,
            status=FloatingIpStatus.DOWN,
            address=floating_ip_address,
        )
        floating_ip: FloatingIp = await self.floating_ip_repository.create(session, floating_ip=floating_ip)

        return FloatingIpResponse.from_entity(floating_ip)
