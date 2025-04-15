import pytest

from domain.project.entity import Project
from domain.user.entity import User
from exception.auth_exception import InvalidAuthException
from test.util.factory import create_user
from test.util.random import random_int, random_string


async def test_authenticate_user_success(mock_session, mock_user_repository, auth_service):
    # given
    account_id = random_string()
    password = random_string()
    expected_result: User = create_user(
        domain_id=random_int(),
        account_id=account_id,
        plain_password=password,
    )
    mock_user_repository.find_by_account_id.return_value = expected_result

    # when
    actual_result: tuple[User, list[Project]] = await auth_service.authenticate_user_and_load_projects(
        session=mock_session,
        account_id=account_id,
        password=password,
    )

    # then
    mock_user_repository.find_by_account_id.assert_called_once_with(
        session=mock_session,
        account_id=account_id,
        with_relations=True,
    )
    assert actual_result[0] == expected_result


async def test_authenticate_user_fail_using_invalid_account_id(mock_session, mock_user_repository, auth_service):
    # given
    invalid_account_id: str = random_string()
    password: str = random_string()
    mock_user_repository.find_by_account_id.return_value = None

    # when & then
    with pytest.raises(InvalidAuthException):
        await auth_service.authenticate_user_and_load_projects(
            session=mock_session,
            account_id=invalid_account_id,
            password=password,
        )
    mock_user_repository.find_by_account_id.assert_called_once_with(
        session=mock_session,
        account_id=invalid_account_id,
        with_relations=True,
    )


async def test_authenticate_user_fail_using_invalid_password(mock_session, mock_user_repository, auth_service):
    # given
    account_id: str = random_string()
    valid_password: str = random_string()
    invalid_password: str = random_string()
    expected_result: User = create_user(
        domain_id=random_int(),
        account_id=account_id,
        plain_password=valid_password,
    )
    mock_user_repository.find_by_account_id.return_value = expected_result

    # when & then
    with pytest.raises(InvalidAuthException):
        await auth_service.authenticate_user_and_load_projects(
            session=mock_session,
            account_id=account_id,
            password=invalid_password,
        )
    mock_user_repository.find_by_account_id.assert_called_once_with(
        session=mock_session,
        account_id=account_id,
        with_relations=True,
    )
