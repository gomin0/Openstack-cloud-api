from sqlalchemy import select, exists, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.enum import LifecycleStatus
from common.domain.volume.entity import Volume


class VolumeRepository:
    async def exists_by_name_and_project(self, session: AsyncSession, name: str, project_id: int) -> bool:
        is_not_deleted: ColumnElement = Volume.lifecycle_status == LifecycleStatus.ACTIVE
        return await session.scalar(
            select(
                exists()
                .where(is_not_deleted, Volume.name == name, Volume.project_id == project_id)
            )
        )

    async def find_by_id(self, session: AsyncSession, volume_id: int) -> Volume | None:
        return await session.scalar(
            select(Volume).where(
                Volume.lifecycle_status == LifecycleStatus.ACTIVE,
                Volume.id == volume_id
            )
        )

    async def find_by_openstack_id(self, session: AsyncSession, openstack_id: str) -> Volume | None:
        return await session.scalar(
            select(Volume).where(
                Volume.lifecycle_status == LifecycleStatus.ACTIVE,
                Volume.openstack_id == openstack_id
            )
        )

    async def create(self, session: AsyncSession, volume: Volume) -> Volume:
        session.add(volume)
        await session.flush()
        return volume
