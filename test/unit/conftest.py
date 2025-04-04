from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.project_service import ProjectService
from application.user_service import UserService


@pytest.fixture(scope='function')
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.begin = AsyncMock()
    return mock_session


@pytest.fixture(scope='function')
def mock_project_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_user_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def project_service(mock_project_repository):
    return ProjectService(project_repository=mock_project_repository)


@pytest.fixture(scope='function')
def user_service(mock_user_repository):
    return UserService(user_repository=mock_user_repository)
