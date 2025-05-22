from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from api_server.main import app
from common.domain.entity import BaseEntity
from common.infrastructure.async_client import get_async_client
from common.infrastructure.database import get_db_session


@pytest.fixture(scope="session")
def mysql_container():
    with MySqlContainer("mysql:8.0") as container:
        container.start()
        yield container


@pytest_asyncio.fixture(scope="session")
async def async_engine(mysql_container):
    async_db_url: str = mysql_container.get_connection_url().replace("mysql://", "mysql+aiomysql://")
    engine = create_async_engine(url=async_db_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_session_maker(async_engine):
    yield sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(async_session_maker):
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_data_before_test(db_session):
    for table in reversed(BaseEntity.metadata.sorted_tables):
        await db_session.execute(table.delete())
    await db_session.commit()
    yield


@pytest_asyncio.fixture(scope="function")
async def mock_async_client():
    return AsyncMock(spec=AsyncClient)


@pytest_asyncio.fixture(scope="function")
async def app_test(mocker, async_session_maker, mock_async_client):
    async def override_get_db_session():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_async_client] = lambda: mock_async_client

    system_keystone_token: str = "keystone-token"
    mocker.patch("common.application.user.service.get_system_keystone_token", return_value=system_keystone_token)
    mocker.patch("common.application.project.service.get_system_keystone_token", return_value=system_keystone_token)
    mocker.patch("common.application.server.service.get_system_keystone_token", return_value=system_keystone_token)
    mocker.patch("common.application.volume.service.get_system_keystone_token", return_value=system_keystone_token)

    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)

    mocker.patch("common.infrastructure.openstack_client.get_async_client", return_value=mock_async_client)

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(app_test):
    async with AsyncClient(
        transport=ASGITransport(app=app_test),
        base_url="http://test",
    ) as client:
        yield client
