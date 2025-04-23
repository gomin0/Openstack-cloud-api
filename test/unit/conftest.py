from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.service import AuthService
from application.project.service import ProjectService
from application.security_group.service import SecurityGroupService
from application.user.service import UserService


@pytest.fixture(scope="session")
def mock_compensation_manager():
    mock = Mock()
    mock.add_task.return_value = None
    return mock


@pytest.fixture(scope='function')
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.begin = AsyncMock()
    return mock_session


@pytest.fixture(scope='function')
def mock_async_client():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_project_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_user_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_project_user_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_security_group_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_keystone_client():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_neutron_client():
    return AsyncMock()


@pytest.fixture(scope='function')
def project_service(mock_project_repository, mock_user_repository, mock_project_user_repository, mock_keystone_client):
    return ProjectService(
        project_repository=mock_project_repository,
        user_repository=mock_user_repository,
        project_user_repository=mock_project_user_repository,
        keystone_client=mock_keystone_client
    )


@pytest.fixture(scope='function')
def user_service(mock_user_repository, mock_keystone_client):
    return UserService(user_repository=mock_user_repository, keystone_client=mock_keystone_client)


@pytest.fixture(scope='function')
def auth_service(mock_user_repository, mock_keystone_client):
    return AuthService(user_repository=mock_user_repository, keystone_client=mock_keystone_client)


@pytest.fixture(scope='function')
def security_group_service(
    mock_security_group_repository,
    mock_project_repository,
    mock_neutron_client
):
    return SecurityGroupService(
        security_group_repository=mock_security_group_repository,
        project_repository=mock_project_repository,
        neutron_client=mock_neutron_client
    )
