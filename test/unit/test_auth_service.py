import pytest

from common.application.auth.response import LoginResponse
from common.domain.project.entity import Project
from common.domain.user.entity import User
from common.exception.auth_exception import InvalidAuthException
from common.exception.project_exception import ProjectAccessDeniedException
from common.exception.user_exception import UserNotJoinedAnyProjectException
from test.util.factory import create_project, create_user_stub
from test.util.random import random_int, random_string


async def test_login_success_with_project_id(
    mock_session,
    mock_async_client,
    mock_user_repository,
    mock_keystone_client,
    auth_service
):
    # given
    domain_id: int = random_int()
    project_id: int = random_int()
    account_id: str = random_string()
    password: str = random_string()

    joined_project: Project = create_project(domain_id=domain_id, project_id=project_id)
    user: User = create_user_stub(
        user_id=random_int(),
        domain_id=domain_id,
        account_id=account_id,
        plain_password=password,
        projects=[joined_project]
    )

    mock_user_repository.find_by_account_id.return_value = user
    mock_keystone_client.authenticate_with_scoped_auth.return_value = "keystone-token", "2025-01-01T00:00:00.000000Z"

    # when
    result: LoginResponse = await auth_service.login(
        session=mock_session,
        client=mock_async_client,
        project_id=project_id,
        account_id=account_id,
        password=password,
    )

    # then
    mock_user_repository.find_by_account_id.assert_called_once()
    mock_keystone_client.authenticate_with_scoped_auth.assert_called_once()
    assert result.user.id == user.id
    assert result.token is not None


async def test_login_success_without_project_id(
    mock_session,
    mock_async_client,
    mock_user_repository,
    mock_keystone_client,
    auth_service
):
    # given
    domain_id: int = random_int()
    account_id: str = random_string()
    password: str = random_string()

    joined_project: Project = create_project(domain_id=domain_id, project_id=random_int())
    user: User = create_user_stub(
        user_id=random_int(),
        domain_id=domain_id,
        account_id=account_id,
        plain_password=password,
        projects=[joined_project]
    )

    mock_user_repository.find_by_account_id.return_value = user
    mock_keystone_client.authenticate_with_scoped_auth.return_value = "keystone-token", "2025-01-01T00:00:00.000000Z"

    # when
    result: LoginResponse = await auth_service.login(
        session=mock_session,
        client=mock_async_client,
        project_id=None,
        account_id=account_id,
        password=password,
    )

    # then
    mock_user_repository.find_by_account_id.assert_called_once()
    mock_keystone_client.authenticate_with_scoped_auth.assert_called_once()
    assert result.user.id == user.id
    assert result.token is not None


async def test_login_fail_using_invalid_account_id(
    mock_session,
    mock_async_client,
    mock_user_repository,
    mock_keystone_client,
    auth_service
):
    # given
    mock_user_repository.find_by_account_id.return_value = None

    # when & then
    with pytest.raises(InvalidAuthException):
        await auth_service.login(
            session=mock_session,
            client=mock_async_client,
            project_id=None,
            account_id=random_string(),
            password=random_string(),
        )
    mock_user_repository.find_by_account_id.assert_called_once()


async def test_login_fail_using_invalid_password(
    mock_session,
    mock_async_client,
    mock_user_repository,
    mock_keystone_client,
    auth_service
):
    # given
    account_id: str = random_string()
    valid_password: str = random_string()
    invalid_password: str = random_string()
    user: User = create_user_stub(
        domain_id=random_int(),
        account_id=account_id,
        plain_password=valid_password,
    )
    mock_user_repository.find_by_account_id.return_value = user

    # when & then
    with pytest.raises(InvalidAuthException):
        await auth_service.login(
            session=mock_session,
            client=mock_async_client,
            project_id=None,
            account_id=random_string(),
            password=invalid_password,
        )
    mock_user_repository.find_by_account_id.assert_called_once()


async def test_login_fail_user_did_not_join_any_project(
    mock_session,
    mock_async_client,
    mock_user_repository,
    mock_keystone_client,
    auth_service
):
    # given
    account_id: str = random_string()
    password: str = random_string()
    user: User = create_user_stub(
        domain_id=random_int(),
        account_id=account_id,
        plain_password=password,
        projects=[]
    )
    mock_user_repository.find_by_account_id.return_value = user

    # when & then
    with pytest.raises(UserNotJoinedAnyProjectException):
        await auth_service.login(
            session=mock_session,
            client=mock_async_client,
            project_id=None,
            account_id=random_string(),
            password=password,
        )
    mock_user_repository.find_by_account_id.assert_called_once()


async def test_login_fail_has_not_project_access_permission(
    mock_session,
    mock_async_client,
    mock_user_repository,
    mock_keystone_client,
    auth_service
):
    # given
    account_id: str = random_string()
    password: str = random_string()
    user: User = create_user_stub(
        domain_id=random_int(),
        account_id=account_id,
        plain_password=password,
    )
    mock_user_repository.find_by_account_id.return_value = user

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await auth_service.login(
            session=mock_session,
            client=mock_async_client,
            project_id=random_int(),
            account_id=random_string(),
            password=password,
        )
    mock_user_repository.find_by_account_id.assert_called_once()
