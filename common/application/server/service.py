import asyncio
import logging
import uuid
from logging import Logger
from typing import Coroutine

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.server.dto import CreateServerCommand
from common.application.server.response import ServerDetailsResponse, ServerDetailResponse, ServerResponse, \
    DeleteServerResponse
from common.domain.enum import SortOrder
from common.domain.network_interface.dto import OsNetworkInterfaceDto
from common.domain.network_interface.entity import NetworkInterface
from common.domain.security_group.entity import SecurityGroup
from common.domain.server.dto import OsServerDto
from common.domain.server.entity import Server
from common.domain.server.enum import ServerSortOption
from common.domain.server.enum import ServerStatus
from common.domain.volume.dto import OsVolumeDto
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.server_exception import ServerNotFoundException, ServerNameDuplicateException, \
    VolumeDetachFailedException, ServerDeletionFailedException
from common.exception.volume_exception import VolumeAttachmentFailedException, VolumeNotFoundException
from common.infrastructure.cinder.client import CinderClient
from common.infrastructure.database import transactional
from common.infrastructure.network_interface.repository import NetworkInterfaceRepository
from common.infrastructure.neutron.client import NeutronClient
from common.infrastructure.nova.client import NovaClient
from common.infrastructure.security_group.repository import SecurityGroupRepository
from common.infrastructure.server.repository import ServerRepository
from common.infrastructure.volume.repository import VolumeRepository
from common.util.compensating_transaction import CompensationManager
from common.util.envs import Envs, get_envs
from common.util.system_token_manager import get_system_keystone_token

envs: Envs = get_envs()
logger: Logger = logging.getLogger(__name__)


class ServerService:
    MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT: int = envs.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT
    CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT: int = envs.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT

    MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE: int = envs.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE
    CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE: int = envs.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE

    MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION: int = envs.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION
    CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION: int = envs.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION

    MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION: int = envs.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION
    CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION: int = envs.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION
    MAX_CHECK_ATTEMPTS_FOR_VOLUME_ATTACHMENT: int = envs.MAX_CHECK_ATTEMPTS_FOR_VOLUME_ATTACHMENT
    CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT: int = envs.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT

    def __init__(
        self,
        server_repository: ServerRepository = Depends(),
        volume_repository: VolumeRepository = Depends(),
        network_interface_repository: NetworkInterfaceRepository = Depends(),
        security_group_repository: SecurityGroupRepository = Depends(),
        nova_client: NovaClient = Depends(),
        neutron_client: NeutronClient = Depends(),
        cinder_client: CinderClient = Depends(),
    ):
        self.server_repository = server_repository
        self.volume_repository = volume_repository
        self.network_interface_repository = network_interface_repository
        self.security_group_repository = security_group_repository
        self.nova_client = nova_client
        self.neutron_client = neutron_client
        self.cinder_client = cinder_client

    @transactional()
    async def find_servers_details(
        self,
        session: AsyncSession,
        id_: int | None,
        ids_contain: list[int] | None,
        ids_exclude: list[int] | None,
        name_eq: str | None,
        name_like: str | None,
        sort_by: ServerSortOption,
        order: SortOrder,
        project_id: int,
    ) -> ServerDetailsResponse:
        servers: list[Server] = await self.server_repository.find_all_by_project_id(
            session=session,
            id_=id_,
            ids_contain=ids_contain,
            ids_exclude=ids_exclude,
            name_eq=name_eq,
            name_like=name_like,
            sort_by=sort_by,
            order=order,
            project_id=project_id,
            with_relations=True,
        )
        return ServerDetailsResponse(servers=[await ServerDetailResponse.from_entity(server) for server in servers])

    @transactional()
    async def get_server_detail(
        self,
        session: AsyncSession,
        server_id: int,
        project_id: int,
    ) -> ServerDetailResponse:
        server: Server | None = await self._get_server_by_id(session=session, id_=server_id, with_relations=True)
        server.validate_access_permission(project_id=project_id)

        return await ServerDetailResponse.from_entity(server)

    @transactional()
    async def get_server(
        self,
        session: AsyncSession,
        server_id: int,
        project_id: int,
    ) -> ServerResponse:
        server: Server = await self.server_repository.find_by_id(
            session=session,
            server_id=server_id,
        )
        if server is None:
            raise ServerNotFoundException()
        server.validate_access_permission(project_id=project_id)

        return ServerResponse.from_entity(server)

    async def get_vnc_console(
        self,
        keystone_token: str,
        server_openstack_id: str,
    ) -> str:
        vnc_url: str = await self.nova_client.get_vnc_console(
            keystone_token=keystone_token,
            server_openstack_id=server_openstack_id
        )

        return vnc_url

    @transactional()
    async def create_server(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        command: CreateServerCommand,
    ) -> ServerResponse:
        """
        요청 정보를 받아 서버를 생성합니다.

        서버가 생성될 때 다음 작업들이 함꼐 진행됩니다.

        - Network Interface 생성
        - Network Interface에 Security Groups 적용
        - 루트 볼륨 생성
        - 서버에 루트 볼륨 연결
        - 서버에 Network Interface 연결

        서버 생성 작업은 비동기로 동작하기에, `ServerService.finalize_server_creation()`를 통해 후처리 작업을 진행해야 합니다.

        :return: 생성된 서버 정보
        """
        is_exists_name: bool = await self.server_repository.exists_by_project_and_name(
            session=session,
            project_id=command.current_project_id,
            name=command.name,
        )
        if is_exists_name:
            raise ServerNameDuplicateException()

        security_groups: list[SecurityGroup] = await self.security_group_repository.find_all_by_ids(
            session=session,
            ids=command.security_group_ids
        )
        for sg in security_groups:
            sg.validate_accessible_by(project_id=command.current_project_id)

        os_network_interface: OsNetworkInterfaceDto = await self.neutron_client.create_network_interface(
            keystone_token=command.keystone_token,
            network_openstack_id=command.network_openstack_id,
            security_group_openstack_ids=[sg.openstack_id for sg in security_groups],
        )
        compensating_tx.add_task(
            lambda: self.neutron_client.delete_network_interface(
                keystone_token=command.keystone_token,
                network_interface_openstack_id=os_network_interface.openstack_id
            )
        )

        server_openstack_id: str = await self.nova_client.create_server(
            keystone_token=command.keystone_token,
            flavor_openstack_id=command.flavor_openstack_id,
            image_openstack_id=command.root_volume.image_openstack_id,
            network_interface_openstack_id=os_network_interface.openstack_id,
            root_volume_size=command.root_volume.size
        )
        compensating_tx.add_task(
            lambda: self.nova_client.delete_server(
                keystone_token=command.keystone_token,
                server_openstack_id=server_openstack_id,
            )
        )

        server: Server = await self.server_repository.create(
            session=session,
            server=Server.create(
                openstack_id=server_openstack_id,
                project_id=command.current_project_id,
                flavor_openstack_id=command.flavor_openstack_id,
                name=command.name,
                description=command.description,
            )
        )
        network_interface: NetworkInterface = await self.network_interface_repository.create(
            session=session,
            network_interface=NetworkInterface.create(
                openstack_id=os_network_interface.openstack_id,
                project_id=command.current_project_id,
                server_id=server.id,
                fixed_ip_address=os_network_interface.fixed_ip_address,
            )
        )
        await network_interface.add_security_groups(security_groups=security_groups)

        return ServerResponse.from_entity(server)

    @transactional()
    async def update_server_info(
        self,
        session: AsyncSession,
        current_project_id: int,
        server_id: int,
        name: str,
        description: str,
    ) -> ServerResponse:
        server: Server | None = await self._get_server_by_id(session=session, id_=server_id)
        server.validate_update_permission(project_id=current_project_id)

        if name != server.name:
            if await self.server_repository.exists_by_project_and_name(
                session=session,
                project_id=current_project_id,
                name=name
            ):
                raise ServerNameDuplicateException()

        server.update_info(name=name, description=description)
        return ServerResponse.from_entity(server)

    async def detach_volume_from_server(
        self,
        session: AsyncSession,
        keystone_token: str,
        project_openstack_id: str,
        project_id: int,
        server_id: int,
        volume_id: int
    ) -> ServerDetailResponse:
        server: Server
        volume: Volume
        server, volume = await self._initiate_volume_detachment(
            session=session,
            keystone_token=keystone_token,
            project_id=project_id,
            server_id=server_id,
            volume_id=volume_id,
        )
        is_success: bool = await self._wait_until_volume_detachment_and_finalize(
            session=session,
            project_openstack_id=project_openstack_id,
            volume_openstack_id=volume.openstack_id
        )
        if not is_success:
            raise VolumeDetachFailedException()
        return await ServerDetailResponse.from_entity(server)

    @transactional()
    async def _initiate_volume_detachment(
        self,
        session: AsyncSession,
        keystone_token: str,
        project_id: int,
        server_id: int,
        volume_id: int
    ) -> tuple[Server, Volume]:
        volume: Volume = await self._get_volume_by_id(session=session, volume_id=volume_id)
        volume.validate_owned_by(project_id=project_id)
        volume.validate_server_match(server_id=server_id)
        volume.prepare_for_detachment()

        server: Server = await self._get_server_by_id(session=session, id_=server_id)
        await self.nova_client.detach_volume_from_server(
            keystone_token=keystone_token,
            server_openstack_id=server.openstack_id,
            volume_openstack_id=volume.openstack_id,
        )

        return server, volume

    @transactional()
    async def _wait_until_volume_detachment_and_finalize(
        self,
        session: AsyncSession,
        client: AsyncClient,
        volume_openstack_id: str,
        project_openstack_id: str
    ) -> bool:
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT)

            os_volume: OsVolumeDto = await self.cinder_client.get_volume(
                keystone_token=get_system_keystone_token(),
                project_openstack_id=project_openstack_id,
                volume_openstack_id=volume_openstack_id,
            )

            if os_volume.status in [VolumeStatus.IN_USE, VolumeStatus.DETACHING]:
                continue
            if os_volume.status == VolumeStatus.AVAILABLE:
                volume: Volume = \
                    await self._get_volume_by_openstack_id(session=session, openstack_id=volume_openstack_id)
                volume.detach_from_server()
                return True
            logger.error(f"볼륨({volume_openstack_id}) 연결 해제 도중 에러가 발생했습니다. status={os_volume.status}")
            volume: Volume = await self._get_volume_by_openstack_id(session=session, openstack_id=volume_openstack_id)
            volume.update_status(status=os_volume.status)
            return False

        logger.error(
            f"볼륨({volume_openstack_id}) 연결 해제를 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DETACHMENT * self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DETACHMENT}초 동안 "
            f"정상적으로 해제되지 않았습니다."
        )
        return False

    @transactional()
    async def start_server(
        self,
        session: AsyncSession,
        keystone_token: str,
        project_id: int,
        server_id: int,
    ) -> ServerResponse:
        server: Server = await self._get_server_by_id(session=session, id_=server_id)
        server.validate_access_permission(project_id=project_id)
        server.validate_startable()
        await self.nova_client.start_server(
            keystone_token=keystone_token, server_openstack_id=server.openstack_id
        )

        return ServerResponse.from_entity(server)

    @transactional()
    async def stop_server(
        self,
        session: AsyncSession,
        keystone_token: str,
        project_id: int,
        server_id: int,
    ) -> ServerResponse:
        server: Server = await self._get_server_by_id(session=session, id_=server_id)
        server.validate_access_permission(project_id=project_id)
        server.validate_stoppable()
        await self.nova_client.stop_server(
            keystone_token=keystone_token, server_openstack_id=server.openstack_id
        )

        return ServerResponse.from_entity(server)

    @transactional()
    async def wait_until_server_started(
        self,
        session: AsyncSession,
        server_openstack_id: str,
    ) -> bool:
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE)

            os_server: OsServerDto = await self.nova_client.get_server(
                keystone_token=get_system_keystone_token(),
                server_openstack_id=server_openstack_id,
            )

            if os_server.status == ServerStatus.SHUTOFF or os_server.status == ServerStatus.ERROR:
                continue

            if os_server.status == ServerStatus.ACTIVE:
                server: Server = await self._get_server_by_openstack_id(
                    session=session, openstack_id=server_openstack_id
                )
                server.start()
                return True
            logger.error(f"서버({server_openstack_id}) 시작 도중 에러가 발생했습니다. status={os_server.status}")
            return False

        logger.error(
            f"서버({server_openstack_id}) 시작을 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE}초 동안 "
            f"정상적으로 시작되지 않았습니다."
        )
        return False

    @transactional()
    async def wait_until_server_stopped(
        self,
        session: AsyncSession,
        server_openstack_id: str,
    ) -> bool:
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE)

            os_server: OsServerDto = await self.nova_client.get_server(
                keystone_token=get_system_keystone_token(),
                server_openstack_id=server_openstack_id,
            )

            if os_server.status == ServerStatus.ACTIVE:
                continue
            if os_server.status == ServerStatus.SHUTOFF:
                server: Server = await self._get_server_by_openstack_id(
                    session=session, openstack_id=server_openstack_id
                )
                server.stop()
                return True
            logger.error(f"서버({server_openstack_id}) 중지 도중 에러가 발생했습니다. status={os_server.status}")
            return False

        logger.error(
            f"서버({server_openstack_id}) 중지를 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_STATUS_UPDATE * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_STATUS_UPDATE}초 동안 "
            f"정상적으로 중지되지 않았습니다."
        )
        return False

    @transactional()
    async def finalize_server_creation(
        self,
        session: AsyncSession,
        client: AsyncClient,
        server_openstack_id: str,
        image_openstack_id: str,
        root_volume_size: int
    ) -> None:
        """
        `ServerService.create_server()`에서 서버 생성을 한 후, 서버 생성이 완료될 때까지 대기합니다.

        이후 서버 생성이 완료되었다면, 서버 생성 완료 후에 처리해야 할 작업들을 수행합니다.

        - 서버를 활성(ACTIVE) 상태로 변경
        - 볼륨 데이터를 DB에 생성(INSERT)
        """
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION)

            os_server: OsServerDto = await self.nova_client.get_server(
                keystone_token=get_system_keystone_token(),
                server_openstack_id=server_openstack_id,
            )

            if os_server.status == ServerStatus.BUILD:
                continue

            if os_server.status == ServerStatus.ACTIVE:
                root_volume_openstack_id: str = os_server.volume_openstack_ids[0]

                server: Server = \
                    await self._get_server_by_openstack_id(session=session, openstack_id=server_openstack_id)
                server.active()
                await self.volume_repository.create(
                    session=session,
                    # 서버 생성 시, volume type을 받게 된다면, 하드 코딩된 값 수정 필요
                    volume=Volume.create(
                        openstack_id=root_volume_openstack_id,
                        project_id=server.project_id,
                        server_id=server.id,
                        volume_type_openstack_id="64a19e22-a30b-4982-8f82-332e89ff4bf7",
                        image_openstack_id=image_openstack_id,
                        name=f"volume_{uuid.uuid4()}",
                        description="",
                        status=VolumeStatus.AVAILABLE,
                        size=root_volume_size,
                        is_root_volume=True,
                    )
                )
                return

            logger.error(f"서버 생성에 실패했습니다. Server openstack_id={server_openstack_id} status={os_server.status}")
            break
        else:
            logger.error(
                f"서버 생성에 실패했습니다. 생성중인 서버 {server_openstack_id}가 "
                f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_CREATION * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION}초 "
                f"동안 생성이 완료되기를 기다렸으나, 생성이 완료되지 않았습니다."
            )
        server: Server = await self._get_server_by_openstack_id(session=session, openstack_id=server_openstack_id)
        server.fail_creation()

    async def attach_volume_to_server(
        self,
        session: AsyncSession,
        keystone_token: str,
        current_project_id: int,
        current_project_openstack_id: str,
        server_id: int,
        volume_id: int,
    ) -> ServerDetailResponse:
        server: Server
        volume: Volume
        server, volume = await self._initiate_volume_attachment(
            session=session,
            keystone_token=keystone_token,
            current_project_id=current_project_id,
            server_id=server_id,
            volume_id=volume_id,
        )
        is_success: bool = await self._wait_until_volume_attachment_and_finalize(
            session=session,
            current_project_openstack_id=current_project_openstack_id,
            server_openstack_id=server.openstack_id,
            volume_openstack_id=volume.openstack_id,
        )
        if not is_success:
            raise VolumeAttachmentFailedException(server_id=server.id, volume_id=volume.id)
        return await ServerDetailResponse.from_entity(server)

    @transactional()
    async def delete_server(
        self,
        session: AsyncSession,
        keystone_token: str,
        server_id: int,
        project_id: int
    ) -> DeleteServerResponse:
        server: Server = await self._get_server_by_id(session=session, id_=server_id)
        server.validate_delete_permission(project_id=project_id)

        network_interfaces: list[NetworkInterface] = await server.network_interfaces
        network_interface_ids: list[int] = [network_interface.id for network_interface in network_interfaces]

        volumes: list[Volume] = await server.volumes
        root_volume_id: int | None = next((volume.id for volume in volumes if volume.is_root_volume), None)

        await self.nova_client.delete_server(
            keystone_token=keystone_token,
            server_openstack_id=server.openstack_id,
        )

        return DeleteServerResponse(
            server_id=server.id,
            volume_id=root_volume_id,
            network_interface_ids=network_interface_ids,
        )

    async def check_server_until_deleted_and_remove_resources(
        self,
        session: AsyncSession,
        keystone_token: str,
        network_interface_ids: list[int],
        server_id: int,
    ) -> None:
        await self._remove_server_resources(
            session=session,
            keystone_token=keystone_token,
            server_id=server_id,
            network_interface_ids=network_interface_ids,
        )
        await self._wait_server_until_deleted_and_finalize(
            session=session,
            server_id=server_id,
        )

    @transactional()
    async def _wait_server_until_deleted_and_finalize(
        self,
        session: AsyncSession,
        server_id: int,
    ) -> None:
        server: Server = await self._get_server_by_id(session=session, id_=server_id)

        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION):
            is_server_deleted: bool = not await self.nova_client.exists_server(
                keystone_token=get_system_keystone_token(),
                server_openstack_id=server.openstack_id,
            )
            if is_server_deleted:
                server.delete()
                return
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION)
        logger.error(
            f"서버({server.openstack_id})를 삭제 시도했으나, "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_SERVER_DELETION * self.CHECK_INTERVAL_SECONDS_FOR_SERVER_DELETION}초 동안 "
            f"정상적으로 삭제되지 않았습니다."
        )
        raise ServerDeletionFailedException()

    @transactional()
    async def _remove_server_resources(
        self,
        session: AsyncSession,
        keystone_token: str,
        server_id: int,
        network_interface_ids: list[int],
    ) -> None:
        server: Server = await self._get_server_by_id(session=session, id_=server_id)
        volumes: list[Volume] = await server.volumes
        for volume in volumes:
            volume.detach_from_server()

        network_interfaces: list[NetworkInterface] = await self.network_interface_repository.find_all_by_ids(
            session=session, network_interface_ids=network_interface_ids
        )
        for network_interface in network_interfaces:
            await network_interface.delete()
            if floating_ip := await network_interface.floating_ip:
                floating_ip.detach_from_network_interface()

        delete_network_interface_tasks: list[Coroutine] = [
            self.neutron_client.delete_network_interface(
                keystone_token=keystone_token,
                network_interface_openstack_id=network_interface.openstack_id
            )
            for network_interface in network_interfaces
        ]
        await asyncio.gather(*delete_network_interface_tasks)

    @transactional()
    async def _initiate_volume_attachment(
        self,
        session: AsyncSession,
        keystone_token: str,
        current_project_id: int,
        server_id: int,
        volume_id: int,
    ) -> tuple[Server, Volume]:
        """
        볼륨 연결을 위한, 다음의 초기 작업을 수행합니다.

        - 볼륨 상태를 `ATTACHING` 으로 변경
        - OpenStack에 서버와 볼륨 연결 요청 (async API)

        볼륨 연결 작업은 비동기로 동작하기에,
        `ServerService.wait_until_volume_attachment_and_finalize()`를 사용해 후처리 작업을 진행해야 합니다.

        :return: 연결하는 서버와 볼륨 객체
        """
        server: Server = await self._get_server_by_id(session=session, id_=server_id)
        server.validate_update_permission(project_id=current_project_id)

        volume: Volume = await self._get_volume_by_id(session=session, volume_id=volume_id)
        volume.validate_update_permission(project_id=current_project_id)

        volume.prepare_for_attachment()

        await self.nova_client.attach_volume_to_server(
            keystone_token=keystone_token,
            server_openstack_id=server.openstack_id,
            volume_openstack_id=volume.openstack_id,
        )

        return server, volume

    @transactional()
    async def _wait_until_volume_attachment_and_finalize(
        self,
        session: AsyncSession,
        current_project_openstack_id: str,
        server_openstack_id: str,
        volume_openstack_id: str,
    ) -> bool:
        """
        `ServerService.initiate_volume_attachment()`에서 볼륨 연결 요청을 한 후,
        OpenStack에서 볼륨 연결이 완료될 때까지 대기합니다.

        볼륨 연결이 완료되었다면, 볼륨 연결 완료 후에 처리해야 할 다음과 같은 작업들을 수행합니다.

        - 볼륨의 상태를 `IN_USE` 로 변경
        - DB에서 볼륨과 서버를 연결
        """
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_ATTACHMENT):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT)
            os_volume: OsVolumeDto = await self.cinder_client.get_volume(
                keystone_token=get_system_keystone_token(),
                project_openstack_id=current_project_openstack_id,
                volume_openstack_id=volume_openstack_id,
            )

            if os_volume.status in [VolumeStatus.RESERVED, VolumeStatus.ATTACHING]:
                continue

            if os_volume.status == VolumeStatus.IN_USE:
                server: Server = \
                    await self._get_server_by_openstack_id(session=session, openstack_id=server_openstack_id)
                volume: Volume = \
                    await self._get_volume_by_openstack_id(session=session, openstack_id=volume_openstack_id)
                volume.attach_to_server(server=server)
                return True

            logger.error(
                f"볼륨 {volume_openstack_id}을 서버 {server_openstack_id}에 연결하는데 실패했습니다. "
                f"Volume openstack id={volume_openstack_id}, status={os_volume.status}. "
                f"Target server id={server_openstack_id}"
            )
            volume: Volume = await self.volume_repository.find_by_openstack_id(
                session=session, openstack_id=volume_openstack_id
            )
            volume.update_status(os_volume.status)
            return False

        logger.error(
            f"볼륨 연결에 실패했습니다. 볼륨 {volume_openstack_id}을 서버{server_openstack_id}에 연결되기를 "
            f"{self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_ATTACHMENT * self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT}초 "
            f"동안 기다렸으나, 볼륨 연결이 완료되지 않았습니다."
        )
        volume: Volume = await self.volume_repository.find_by_openstack_id(
            session=session, openstack_id=volume_openstack_id
        )
        volume.fail_attachment()
        return False

    async def _get_server_by_id(
        self,
        session: AsyncSession,
        id_: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> Server:
        if (server := await self.server_repository.find_by_id(session, id_, with_deleted, with_relations)) is None:
            raise ServerNotFoundException()
        return server

    async def _get_server_by_openstack_id(self, session: AsyncSession, openstack_id: str):
        if (server := await self.server_repository.find_by_openstack_id(session, openstack_id)) is None:
            raise ServerNotFoundException()
        return server

    async def _get_volume_by_id(self, session: AsyncSession, volume_id: int) -> Volume:
        if (volume := await self.volume_repository.find_by_id(session, volume_id)) is None:
            raise VolumeNotFoundException()
        return volume

    async def _get_volume_by_openstack_id(self, session, openstack_id):
        if (volume := await self.volume_repository.find_by_openstack_id(session, openstack_id)) is None:
            raise VolumeNotFoundException()
        return volume
