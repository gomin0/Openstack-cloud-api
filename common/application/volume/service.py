import asyncio
import logging
from logging import Logger

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.volume.response import VolumeResponse
from common.domain.volume.dto import VolumeDto
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.openstack_exception import OpenStackException
from common.exception.volume_exception import (
    VolumeNameDuplicateException, VolumeNotFoundException, VolumeDeletionFailedException, VolumeResizingFailedException
)
from common.infrastructure.cinder.client import CinderClient
from common.infrastructure.database import transactional
from common.infrastructure.volume.repository import VolumeRepository
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()
logger: Logger = logging.getLogger(__name__)


class VolumeService:
    # 볼륨 생성 시: 최대 MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION * SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION초 동안 동기화 수행
    MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION: int = envs.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION
    SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION: int = envs.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION

    MAX_CHECK_ATTEMPTS_FOR_VOLUME_DELETION: int = envs.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DELETION
    CHECK_INTERVAL_SECONDS_FOR_VOLUME_DELETION: int = envs.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DELETION

    MAX_CHECK_ATTEMPTS_FOR_VOLUME_RESIZING: int = envs.MAX_CHECK_ATTEMPTS_FOR_VOLUME_RESIZING
    CHECK_INTERVAL_SECONDS_FOR_VOLUME_RESIZING: int = envs.CHECK_INTERVAL_SECONDS_FOR_VOLUME_RESIZING

    def __init__(
        self,
        volume_repository: VolumeRepository = Depends(),
        cinder_client: CinderClient = Depends(),
    ):
        self.volume_repository = volume_repository
        self.cinder_client = cinder_client

    @transactional()
    async def create_volume(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_id: int,
        project_openstack_id: str,
        name: str,
        description: str,
        size: int,
        volume_type_openstack_id: str,
        image_openstack_id: str | None,
    ) -> VolumeResponse:
        is_name_exists: bool = await self.volume_repository.exists_by_name_and_project(
            session, name=name, project_id=project_id
        )
        if is_name_exists:
            raise VolumeNameDuplicateException()

        new_volume_openstack_id: str = await self.cinder_client.create_volume(
            client,
            keystone_token=keystone_token,
            project_openstack_id=project_openstack_id,
            volume_type_openstack_id=volume_type_openstack_id,
            image_openstack_id=image_openstack_id,
            size=size,
        )

        volume: Volume = Volume.create(
            openstack_id=new_volume_openstack_id,
            project_id=project_id,
            server_id=None,
            volume_type_openstack_id=volume_type_openstack_id,
            image_openstack_id=image_openstack_id,
            name=name,
            description=description,
            status=VolumeStatus.CREATING,
            size=size,
            is_root_volume=False,
        )
        volume: Volume = await self.volume_repository.create(session, volume=volume)
        return VolumeResponse.from_entity(volume)

    @transactional()
    async def sync_creating_volume_until_available(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ) -> None:
        """
        OpenStack Cinder API를 통해 생성 중인 볼륨의 상태를 주기적으로 확인하여, 생성이 완료될 때까지 동기화(sync)합니다.

        볼륨 상태가 ``AVAILABLE`` 이 되면 생성 완료로 간주하고, 볼륨 entity의 상태를 ``AVAILABLE`` 로 갱신합니다.
        그 외의 실패 상태로 변경될 경우 생성 실패 처리합니다. 이 경우, entity의 상태를 ``ERROR`` 로 변경합니다.
        최대 시도 횟수를 초과하면 예외를 발생시킵니다.

        :raises TimeoutError: 최대 동기화 시도 횟수(``MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION``)를 초과해도 OpenStack에서 상태 갱신이 완료되지 않은 경우
        :raises VolumeNotFoundException: DB에서 볼륨 정보를 찾을 수 없는 경우
        """
        for _ in range(self.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION):
            status: VolumeStatus = await self.cinder_client.get_volume_status(
                client,
                keystone_token=keystone_token,
                project_openstack_id=project_openstack_id,
                volume_openstack_id=volume_openstack_id
            )
            if status == VolumeStatus.CREATING:
                await asyncio.sleep(self.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION)
                continue

            volume: Volume = await self._get_volume_by_openstack_id(session, openstack_id=volume_openstack_id)
            if status == VolumeStatus.AVAILABLE:
                volume.complete_creation(attached=False)
                break
            elif status == VolumeStatus.ERROR:
                volume.fail_creation()
                break
            else:
                logger.error(f"볼륨 생성 중 정의되지 않은 볼륨 상태를 감지했습니다: {status!r} (volume_id={volume_openstack_id})")
                volume.fail_creation()
                break
        else:
            logger.error(
                f"생성중인 볼륨({volume_openstack_id})의 상태가 "
                f"{self.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION * self.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION}초 동안 "
                f"전환되지 않았습니다."
            )
            volume: Volume = await self._get_volume_by_openstack_id(session, openstack_id=volume_openstack_id)
            volume.fail_creation()

    @transactional()
    async def update_volume_info(
        self,
        session: AsyncSession,
        current_project_id: int,
        volume_id: int,
        name: str,
        description: str,
    ) -> VolumeResponse:
        volume: Volume | None = await self.volume_repository.find_by_id(session=session, volume_id=volume_id)
        if volume is None:
            raise VolumeNotFoundException()
        volume.validate_update_permission(project_id=current_project_id)

        if volume.name != name and await self.volume_repository.exists_by_name_and_project(
            session=session,
            name=name,
            project_id=current_project_id
        ):
            raise VolumeNameDuplicateException()

        volume.update_info(name=name, description=description)
        return VolumeResponse.from_entity(volume)

    async def update_volume_size(
        self,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        current_project_id: int,
        current_project_openstack_id: str,
        volume_id: int,
        new_size: int,
    ) -> VolumeResponse:
        volume: Volume = await self._prepare_volume_for_resize(
            session=session,
            current_project_id=current_project_id,
            volume_id=volume_id,
            new_size=new_size,
        )

        await self.cinder_client.extend_volume_size(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=current_project_openstack_id,
            volume_openstack_id=volume.openstack_id,
            new_size=new_size,
        )

        await self._wait_for_volume_resize_completion(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=current_project_openstack_id,
            volume_openstack_id=volume.openstack_id,
            target_size=new_size,
        )

        await self._resize_and_persist_volume(session, volume=volume, new_size=new_size)

        return VolumeResponse.from_entity(volume)

    @transactional()
    async def delete_volume(
        self,
        session: AsyncSession,
        client: AsyncClient,
        current_project_id: int,
        current_project_openstack_id: str,
        keystone_token: str,
        volume_id: int,
    ) -> None:
        volume: Volume | None = await self.volume_repository.find_by_id(session, volume_id=volume_id)
        if volume is None:
            raise VolumeNotFoundException()
        volume.validate_delete_permission(project_id=current_project_id)
        volume.validate_deletable()

        # (OpenStack) delete volume
        await self.cinder_client.delete_volume(
            client=client,
            keystone_token=keystone_token,
            project_openstack_id=current_project_openstack_id,
            volume_openstack_id=volume.openstack_id,
        )

        # (OpenStack) Check volume is deleted
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_DELETION):
            is_volume_deleted: bool = not await self._exists_volume_from_openstack(
                client=client,
                keystone_token=keystone_token,
                project_openstack_id=current_project_openstack_id,
                volume_openstack_id=volume.openstack_id
            )
            if is_volume_deleted:
                break
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_DELETION)
        else:
            logger.error(
                f"볼륨({volume.openstack_id})을 삭제 시도했으나, "
                f"{self.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION * self.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION}초 동안 "
                f"정상적으로 삭제되지 않았습니다."
            )
            raise VolumeDeletionFailedException()

        # (DB) delete volume
        volume.delete()

    async def _get_volume_by_id(self, session: AsyncSession, volume_id: int) -> Volume:
        if (volume := await self.volume_repository.find_by_id(session, volume_id=volume_id)) is None:
            raise VolumeNotFoundException()
        return volume

    async def _get_volume_by_openstack_id(self, session: AsyncSession, openstack_id: str) -> Volume:
        if (volume := await self.volume_repository.find_by_openstack_id(session, openstack_id=openstack_id)) is None:
            raise VolumeNotFoundException()
        return volume

    async def _exists_volume_from_openstack(
        self,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
    ):
        try:
            await self.cinder_client.get_volume(
                client=client,
                keystone_token=keystone_token,
                project_openstack_id=project_openstack_id,
                volume_openstack_id=volume_openstack_id,
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 404:
                return False
            raise ex
        return True

    @transactional()
    async def _prepare_volume_for_resize(
        self,
        session: AsyncSession,
        current_project_id: int,
        volume_id: int,
        new_size: int,
    ) -> Volume:
        volume: Volume = await self._get_volume_by_id(session=session, volume_id=volume_id)
        volume.validate_update_permission(project_id=current_project_id)
        volume.validate_resizable(size=new_size)
        return volume

    @transactional()
    async def _resize_and_persist_volume(self, _: AsyncSession, volume: Volume, new_size: int):
        volume.resize(size=new_size)

    async def _wait_for_volume_resize_completion(
        self,
        client: AsyncClient,
        keystone_token: str,
        project_openstack_id: str,
        volume_openstack_id: str,
        target_size: int,
    ):
        for _ in range(self.MAX_CHECK_ATTEMPTS_FOR_VOLUME_RESIZING):
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS_FOR_VOLUME_RESIZING)

            vol: VolumeDto = await self.cinder_client.get_volume(
                client=client,
                keystone_token=keystone_token,
                project_openstack_id=project_openstack_id,
                volume_openstack_id=volume_openstack_id,
            )

            if vol.status == VolumeStatus.EXTENDING:
                continue

            is_resize_complete: bool = vol.status == VolumeStatus.AVAILABLE and vol.size == target_size
            if is_resize_complete:
                return

            raise VolumeResizingFailedException()

        raise VolumeResizingFailedException()
