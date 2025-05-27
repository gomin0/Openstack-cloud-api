from typing import Sequence, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def add_to_db(session: AsyncSession, entity: T) -> T:
    session.add(entity)
    await session.flush()
    return entity


async def add_all_to_db(session: AsyncSession, entities: Sequence[T]) -> Sequence[T]:
    session.add_all(entities)
    await session.flush()
    return entities
