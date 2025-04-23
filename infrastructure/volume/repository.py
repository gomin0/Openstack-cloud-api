from sqlalchemy import select, exists, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from domain.enum import LifecycleStatus
from domain.volume.entity import Volume


class VolumeRepository:
    async def exists_by_name(self, session: AsyncSession, name: str) -> bool:
        is_not_deleted: ColumnElement = Volume.lifecycle_status == LifecycleStatus.ACTIVE
        return await session.scalar(
            select(exists().where(is_not_deleted, Volume.name == name))
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
