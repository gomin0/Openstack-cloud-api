from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import declarative_base, sessionmaker

from common.envs import get_envs

envs = get_envs()
Base = declarative_base()

DATABASE_URL = (
    "mysql+aiomysql://"
    f"{envs.database_username}:{envs.database_password}@{envs.database_host}:{envs.database_port}"
    "/cloud"
)
async_engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
