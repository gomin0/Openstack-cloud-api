import pytest

from common.envs import get_envs
from domain.keystone.model import KeystoneToken
from exception.auth_exception import InvalidAuthException
from exception.openstack_exception import OpenStackException
from exception.project_exception import ProjectAccessDeniedException
from test.util.random import random_string


async def test_issue_keystone_token_success(mock_async_client, mock_keystone_client, keystone_service):
    # given
    user_openstack_id: str = random_string()
    password: str = random_string()
    project_openstack_id: str = random_string()
    expected_result: tuple[str, str] = "keystone-token", "2025-01-01T00:00:00.000000Z"
    mock_keystone_client.authenticate_with_scoped_auth.return_value = expected_result

    # when
    actual_result: KeystoneToken = await keystone_service.issue_keystone_token(
        client=mock_async_client,
        user_openstack_id=user_openstack_id,
        password=password,
        project_openstack_id=project_openstack_id,
    )

    # then
    mock_keystone_client.authenticate_with_scoped_auth.assert_called_once_with(
        client=mock_async_client,
        domain_openstack_id=get_envs().DEFAULT_DOMAIN_OPENSTACK_ID,
        user_openstack_id=user_openstack_id,
        password=password,
        project_openstack_id=project_openstack_id,
    )
    assert actual_result.token == expected_result[0]


async def test_issue_keystone_token_fail_keystone_401_error(mock_async_client, mock_keystone_client, keystone_service):
    # given
    user_openstack_id: str = random_string()
    password: str = random_string()
    project_openstack_id: str = random_string()
    mock_keystone_client.authenticate_with_scoped_auth.side_effect = OpenStackException(openstack_status_code=401)

    # when & then
    with pytest.raises(InvalidAuthException):
        await keystone_service.issue_keystone_token(
            client=mock_async_client,
            user_openstack_id=user_openstack_id,
            password=password,
            project_openstack_id=project_openstack_id,
        )
    mock_keystone_client.authenticate_with_scoped_auth.assert_called_once_with(
        client=mock_async_client,
        domain_openstack_id=get_envs().DEFAULT_DOMAIN_OPENSTACK_ID,
        user_openstack_id=user_openstack_id,
        password=password,
        project_openstack_id=project_openstack_id,
    )


async def test_issue_keystone_token_fail_keystone_403_error(mock_async_client, mock_keystone_client, keystone_service):
    # given
    user_openstack_id: str = random_string()
    password: str = random_string()
    project_openstack_id: str = random_string()
    mock_keystone_client.authenticate_with_scoped_auth.side_effect = OpenStackException(openstack_status_code=403)

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await keystone_service.issue_keystone_token(
            client=mock_async_client,
            user_openstack_id=user_openstack_id,
            password=password,
            project_openstack_id=project_openstack_id,
        )
    mock_keystone_client.authenticate_with_scoped_auth.assert_called_once_with(
        client=mock_async_client,
        domain_openstack_id=get_envs().DEFAULT_DOMAIN_OPENSTACK_ID,
        user_openstack_id=user_openstack_id,
        password=password,
        project_openstack_id=project_openstack_id,
    )
