import inspect
import logging
from functools import wraps
from logging import Logger
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from util.envs import get_envs

envs = get_envs()
logger: Logger = logging.getLogger(__name__)

DATABASE_URL = (
    "mysql+aiomysql://"
    f"{envs.DATABASE_USERNAME}:{envs.DATABASE_PASSWORD}@{envs.DATABASE_HOST}:{envs.DATABASE_PORT}"
    "/cloud"
)
async_engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def transactional():
    """
    비동기 함수(`async def`)에 붙여 사용한다.

    `@transactional`은 parameter에 있는 임의의 `AsyncSession` 객체를 사용하여 트랜잭션을 관리한다.

    `@transactional()` decorator가 붙은 함수는 시작 시 트랜잭션이 명시적으로 시작(begin)되며,
    함수 종료 시 자동으로 commit or rollback 된다.

    :raise ValueError: `AsyncSession` type의 parameter가 없거나 None인 경우
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_signature = inspect.signature(func)
            bound_args = func_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            session = None
            for name, value in bound_args.arguments.items():
                if isinstance(value, AsyncSession):
                    session = value
                    break

            if session is None:
                raise ValueError("transactional decorator 사용을 위해서는 함수에 AsyncSession type의 parameter가 존재해야 합니다.")

            try:
                result = await func(*args, **kwargs)
                await session.commit()
                return result
            except Exception as ex:
                logger.error(f"[transactional] '{func.__name__}' 실행 중 예외 발생: {type(ex).__name__}: {ex}")
                await session.rollback()
                raise

        return wrapper

    return decorator
