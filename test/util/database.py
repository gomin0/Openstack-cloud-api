from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession


async def add_to_db[T](session: AsyncSession, entity: T) -> T:
    session.add(entity)
    await session.flush()
    return entity


async def add_all_to_db[T](session: AsyncSession, entities: Sequence[T]) -> Sequence[T]:
    session.add_all(entities)
    await session.flush()
    return entities
