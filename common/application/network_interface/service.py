from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.floating_ip.entity import FloatingIp
from common.domain.network_interface.entity import NetworkInterface
from common.exception.floating_ip_exception import FloatingIpNotFoundException, \
    FloatingIpNotAttachedToNetworkInterfaceException
from common.exception.network_interface_exception import NetworkInterfaceNotFoundException
from common.infrastructure.database import transactional
from common.infrastructure.floating_ip.repository import FloatingIpRepository
from common.infrastructure.network_interface.repository import NetworkInterfaceRepository
from common.infrastructure.neutron.client import NeutronClient
from common.infrastructure.server.repository import ServerRepository
from common.util.compensating_transaction import CompensationManager


class NetworkInterfaceService:
    def __init__(
        self,
        server_repository: ServerRepository = Depends(),
        floating_ip_repository: FloatingIpRepository = Depends(),
        network_interface_repository: NetworkInterfaceRepository = Depends(),
        neutron_client: NeutronClient = Depends(),
    ):
        self.server_repository = server_repository
        self.floating_ip_repository = floating_ip_repository
        self.network_interface_repository = network_interface_repository
        self.neutron_client = neutron_client

    @transactional()
    async def attach_floating_ip_to_network_interface(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        floating_ip_id: int,
        network_interface_id: int,
    ) -> None:
        network_interface: NetworkInterface = await self._get_network_interface_by_id(
            session=session,
            network_interface_id=network_interface_id
        )
        network_interface.validate_access_permission(project_id=project_id)

        floating_ip: FloatingIp = await self._get_floating_ip_by_id(session=session, floating_ip_id=floating_ip_id)
        floating_ip.attach_to_network_interface(network_interface=network_interface)

        await self.neutron_client.attach_floating_ip_to_network_interface(
            client=client,
            keystone_token=keystone_token,
            floating_ip_openstack_id=floating_ip.openstack_id,
            network_interface_id=network_interface.openstack_id
        )
        compensating_tx.add_task(
            lambda: self.neutron_client.detach_floating_ip_from_network_interface(
                client=client,
                keystone_token=keystone_token,
                floating_ip_openstack_id=floating_ip.openstack_id,
            )
        )

    @transactional()
    async def detach_floating_ip_from_network_interface(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        floating_ip_id: int,
        network_interface_id: int,
    ) -> None:
        floating_ip: FloatingIp = await self._get_floating_ip_by_id(session=session, floating_ip_id=floating_ip_id)

        network_interface: NetworkInterface | None = await floating_ip.network_interface
        if network_interface is None:
            raise FloatingIpNotAttachedToNetworkInterfaceException()
        floating_ip.check_network_interface_match(network_interface_id=network_interface_id)
        network_interface.validate_access_permission(project_id=project_id)

        floating_ip.detach_from_network_interface()

        await self.neutron_client.detach_floating_ip_from_network_interface(
            client=client,
            keystone_token=keystone_token,
            floating_ip_openstack_id=floating_ip.openstack_id,
        )
        port_id: str = network_interface.openstack_id
        compensating_tx.add_task(
            lambda: self.neutron_client.attach_floating_ip_to_network_interface(
                client=client,
                keystone_token=keystone_token,
                floating_ip_openstack_id=floating_ip.openstack_id,
                network_interface_id=port_id,
            )
        )

    async def _get_floating_ip_by_id(
        self,
        session: AsyncSession,
        floating_ip_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> FloatingIp:
        if (
            floating_ip := await self.floating_ip_repository.find_by_id(
                session=session,
                floating_ip_id=floating_ip_id,
                with_deleted=with_deleted,
                with_relations=with_relations,
            )
        ) is None:
            raise FloatingIpNotFoundException()
        return floating_ip

    async def _get_network_interface_by_id(
        self,
        session: AsyncSession,
        network_interface_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> NetworkInterface:
        if (
            network_interface := await self.network_interface_repository.find_by_id(
                session=session,
                network_interface_id=network_interface_id,
                with_deleted=with_deleted,
                with_relations=with_relations,
            )
        ) is None:
            raise NetworkInterfaceNotFoundException()
        return network_interface
