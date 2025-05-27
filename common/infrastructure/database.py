import inspect
import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from logging import Logger
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from common.util.envs import get_envs

envs = get_envs()
logger: Logger = logging.getLogger(__name__)

_DATABASE_URL = (
    "mysql+aiomysql://"
    f"{envs.DATABASE_USERNAME}:{envs.DATABASE_PASSWORD}@{envs.DATABASE_HOST}:{envs.DATABASE_PORT}"
    "/cloud"
)
_async_engine: AsyncEngine = create_async_engine(_DATABASE_URL, echo=True)
_async_session: ContextVar[AsyncSession | None] = ContextVar("db_session", default=None)

session_maker: sessionmaker[AsyncSession] = \
    sessionmaker(bind=_async_engine, class_=AsyncSession, autocommit=False, autoflush=False, expire_on_commit=False)


@asynccontextmanager
async def session_factory() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession | None = _async_session.get()

    if session is not None:
        yield session
        return

    session: AsyncSession = session_maker()
    _async_session.set(session)
    try:
        yield session
        await session.commit()
    except Exception as ex:
        await session.rollback()
        raise ex
    finally:
        await session.close()
        _async_session.set(None)


def transactional(func):
    """
    비동기 함수(`async def`)에 붙여 사용한다.

    `@transactional`은 parameter에 있는 임의의 `AsyncSession` 객체를 사용하여 트랜잭션을 관리한다.

    `@transactional` decorator가 붙은 함수는 시작 시 트랜잭션이 명시적으로 시작(begin)되며,
    함수 종료 시 자동으로 commit or rollback 된다.

    :raise ValueError: `AsyncSession` type의 parameter가 없거나 None인 경우
    """
    if not inspect.iscoroutinefunction(func):
        raise TypeError("async_transactional decorator can only be used with async functions")

    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with session_factory():
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as ex:
                logger.error(msg=f"[transactional] '{func.__name__}' 실행 중 예외 발생", exc_info=ex)
                raise
            finally:
                _async_session.set(None)

    return wrapper
