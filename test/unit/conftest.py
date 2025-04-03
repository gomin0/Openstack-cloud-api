from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.project_service import ProjectService


@pytest.fixture(scope='function')
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.begin = AsyncMock()
    return mock_session


@pytest.fixture(scope='function')
def mock_project_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def project_service(mock_project_repository):
    return ProjectService(project_repository=mock_project_repository)
