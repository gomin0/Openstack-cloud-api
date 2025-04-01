import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient
from testcontainers.mysql import MySqlContainer

from domain.entity import Base
from infrastructure.database import get_db_session
from main import app


@pytest.fixture(scope="session")
def mysql_container():
    with MySqlContainer("mysql:8.0") as container:
        container.start()
        yield container


@pytest.fixture(scope="session")
def override_database_url(mysql_container):
    mysql_container_url = mysql_container.get_connection_url()
    return mysql_container_url.replace("mysql://", "mysql+aiomysql://")


@pytest.fixture(scope="session")
async def async_test_engine(override_database_url):
    engine = create_async_engine(override_database_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def async_test_session(async_test_engine):
    yield sessionmaker(
        bind=async_test_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="function")
async def db_session(async_test_session):
    async with async_test_session() as session:
        await session.begin_nested()
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_client(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    client = TestClient(app)
    yield client
