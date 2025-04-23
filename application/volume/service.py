import asyncio
import logging
from logging import Logger

from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.volume.response import VolumeResponse
from common.context import CurrentUser
from common.envs import Envs, get_envs
from domain.volume.entity import Volume
from domain.volume.enum import VolumeStatus
from exception.volume_exception import VolumeNameDuplicateException, VolumeNotFoundException
from infrastructure.cinder.client import CinderClient
from infrastructure.database import transactional
from infrastructure.volume.repository import VolumeRepository

envs: Envs = get_envs()
logger: Logger = logging.getLogger(__name__)


class VolumeService:
    # 볼륨 생성 시: 최대 MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION * SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION초 동안 동기화 수행
    MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION = envs.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION
    SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION = envs.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION

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
        request_user: CurrentUser,
        name: str,
        description: str,
        size: int,
        volume_type_openstack_id: str,
        image_openstack_id: str | None,
    ) -> VolumeResponse:
        is_name_exists: bool = await self.volume_repository.exists_by_name(session, name=name)
        if is_name_exists:
            raise VolumeNameDuplicateException()

        new_volume_openstack_id: str = await self.cinder_client.create_volume(
            client,
            keystone_token=request_user.keystone_token,
            project_openstack_id=request_user.project_openstack_id,
            volume_type_openstack_id=volume_type_openstack_id,
            image_openstack_id=image_openstack_id,
            size=size,
        )

        volume: Volume = Volume.create(
            openstack_id=new_volume_openstack_id,
            project_id=request_user.project_id,
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
            elif status == VolumeStatus.AVAILABLE:
                volume: Volume = await self._get_volume_by_openstack_id(session, openstack_id=volume_openstack_id)
                volume.complete_creation(attached=False)
                break
            elif status == VolumeStatus.ERROR:
                volume: Volume = await self._get_volume_by_openstack_id(session, openstack_id=volume_openstack_id)
                volume.fail_creation()
                break
            else:
                logger.error(f"볼륨 생성 중 정의되지 않은 볼륨 상태를 감지했습니다: {status!r} (volume_id={volume_openstack_id})")
                raise ValueError(f"볼륨 생성 중 정의되지 않은 상태({status!r})가 반환되었습니다. volume_id={volume_openstack_id}")
        else:
            raise TimeoutError(
                f"생성중인 볼륨({volume_openstack_id})의 상태가 "
                f"{self.MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION * self.SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION}초 동안 "
                f"전환되지 않았습니다."
            )

    async def _get_volume_by_openstack_id(
        self,
        session: AsyncSession,
        openstack_id: str,
    ) -> Volume | None:
        volume: Volume | None = await self.volume_repository.find_by_openstack_id(session, openstack_id=openstack_id)
        if volume is None:
            raise VolumeNotFoundException()
        return volume
