from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.auth.service import AuthService
from common.application.floating_ip.service import FloatingIpService
from common.application.network_interface.service import NetworkInterfaceService
from common.application.project.service import ProjectService
from common.application.security_group.service import SecurityGroupService
from common.application.server.service import ServerService
from common.application.user.service import UserService
from common.application.volume.service import VolumeService


@pytest.fixture(scope="session")
def mock_compensation_manager():
    mock = Mock()
    mock.add_task.return_value = None
    return mock


@pytest.fixture(scope="function", autouse=True)
def set_fake_system_keystone_token(mocker):
    system_keystone_token: str = "keystone-token"
    mocker.patch("common.application.user.service.get_system_keystone_token", return_value=system_keystone_token)
    mocker.patch("common.application.project.service.get_system_keystone_token", return_value=system_keystone_token)
    mocker.patch("common.application.server.service.get_system_keystone_token", return_value=system_keystone_token)
    mocker.patch("common.application.volume.service.get_system_keystone_token", return_value=system_keystone_token)


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


@pytest.fixture(scope="function")
def mock_volume_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_security_group_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_network_interface_security_group_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_floating_ip_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_server_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_network_interface_repository():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_keystone_client():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_neutron_client():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_cinder_client():
    return AsyncMock()


@pytest.fixture(scope='function')
def mock_nova_client():
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
    mock_network_interface_security_group_repository,
    mock_neutron_client
):
    return SecurityGroupService(
        security_group_repository=mock_security_group_repository,
        network_interface_security_group_repository=mock_network_interface_security_group_repository,
        neutron_client=mock_neutron_client
    )


@pytest.fixture(scope='function')
def volume_service(mock_volume_repository, mock_cinder_client):
    return VolumeService(volume_repository=mock_volume_repository, cinder_client=mock_cinder_client)


@pytest.fixture(scope='function')
def floating_ip_service(mock_floating_ip_repository, mock_neutron_client):
    return FloatingIpService(
        floating_ip_repository=mock_floating_ip_repository,
        neutron_client=mock_neutron_client
    )


@pytest.fixture(scope='function')
def server_service(
    mock_server_repository,
    mock_volume_repository,
    mock_network_interface_repository,
    mock_security_group_repository,
    mock_nova_client,
    mock_neutron_client,
    mock_cinder_client,
) -> ServerService:
    return ServerService(
        server_repository=mock_server_repository,
        volume_repository=mock_volume_repository,
        network_interface_repository=mock_network_interface_repository,
        security_group_repository=mock_security_group_repository,
        nova_client=mock_nova_client,
        neutron_client=mock_neutron_client,
        cinder_client=mock_cinder_client
    )


@pytest.fixture(scope='function')
def network_interface_service(
    mock_server_repository,
    mock_floating_ip_repository,
    mock_network_interface_repository,
    mock_neutron_client
):
    return NetworkInterfaceService(
        server_repository=mock_server_repository,
        floating_ip_repository=mock_floating_ip_repository,
        network_interface_repository=mock_network_interface_repository,
        neutron_client=mock_neutron_client
    )
