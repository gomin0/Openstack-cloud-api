from sqlalchemy import select, exists, ColumnElement, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from common.domain.volume.entity import Volume


class VolumeRepository:
    async def exists_by_name_and_project(self, session: AsyncSession, name: str, project_id: int) -> bool:
        is_not_deleted: ColumnElement = Volume.deleted_at.is_(None)
        return await session.scalar(
            select(
                exists()
                .where(is_not_deleted, Volume.name == name, Volume.project_id == project_id)
            )
        )

    async def find_by_id(
        self,
        session: AsyncSession,
        volume_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> Volume | None:
        query: Select = select(Volume).where(Volume.id == volume_id)
        if not with_deleted:
            query = query.where(Volume.deleted_at.is_(None))
        if with_relations:
            query = query.options(
                joinedload(Volume._project),
                joinedload(Volume._server),
            )
        return await session.scalar(query)

    async def find_by_openstack_id(self, session: AsyncSession, openstack_id: str) -> Volume | None:
        return await session.scalar(
            select(Volume).where(
                Volume.deleted_at.is_(None),
                Volume.openstack_id == openstack_id
            )
        )

    async def create(self, session: AsyncSession, volume: Volume) -> Volume:
        session.add(volume)
        await session.flush()
        return volume
