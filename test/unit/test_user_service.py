import pytest

from common.domain.enum import SortOrder
from common.domain.user.entity import User
from common.domain.user.enum import UserSortOption
from common.exception.user_exception import (
    UserNotFoundException, UserAccountIdDuplicateException, UserUpdatePermissionDeniedException
)
from test.unit.conftest import mock_session, mock_user_repository, user_service, mock_keystone_client
from test.util.factory import create_user
from test.util.factory import create_user_stub
from test.util.random import random_string, random_int


async def test_find_users(mock_session, mock_user_repository, user_service):
    # given
    domain_id: int = random_int()
    account_id: str = random_string()
    user1 = create_user_stub(user_id=random_int(), domain_id=domain_id)
    user2 = create_user_stub(user_id=random_int(), domain_id=domain_id)
    mock_user_repository.find_all.return_value = [user1, user2]

    # when
    result = await user_service.find_user_details(
        session=mock_session,
        account_id=account_id,
        sort_by=UserSortOption.ACCOUNT_ID,
        sort_order=SortOrder.ASC,
        with_deleted=False,
        with_relations=True
    )

    # then
    assert len(result) == 2
    mock_user_repository.find_all.assert_called_once_with(
        session=mock_session,
        user_id=None,
        account_id=account_id,
        name=None,
        sort_by=UserSortOption.ACCOUNT_ID,
        sort_order=SortOrder.ASC,
        with_deleted=False,
        with_relations=True
    )


async def test_get_user(mock_session, mock_user_repository, user_service):
    # given
    user_id: int = random_int()
    domain_id: int = random_int()
    user = create_user_stub(user_id=random_int(), domain_id=domain_id)

    mock_user_repository.find_by_id.return_value = user

    # when
    result = await user_service.get_user_detail(
        session=mock_session,
        user_id=user_id,
        with_deleted=False,
        with_relations=True
    )

    # then
    assert result.id == user.id
    mock_user_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        user_id=user_id,
        with_deleted=False,
        with_relations=True
    )


async def test_get_user_fail_not_found(mock_session, mock_user_repository, user_service):
    # given
    user_id = 999
    mock_user_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(UserNotFoundException):
        await user_service.get_user_detail(
            session=mock_session,
            user_id=user_id,
            with_deleted=False,
            with_relations=True
        )

    mock_user_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        user_id=user_id,
        with_deleted=False,
        with_relations=True
    )


async def test_create_user_success(
    user_service,
    mock_user_repository,
    mock_keystone_client,
    mock_session,
    mock_compensation_manager,
):
    # given
    expected_result: User = create_user_stub(user_id=random_int(), domain_id=random_int())
    mock_user_repository.exists_by_account_id.return_value = False
    mock_keystone_client.create_user.return_value = "openstack_id"
    mock_user_repository.create.return_value = expected_result

    # when
    actual_result: User = await user_service.create_user(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        account_id=random_string(),
        name=random_string(),
        password=random_string(),
    )

    # then
    mock_user_repository.exists_by_account_id.assert_called_once()
    mock_keystone_client.create_user.assert_called_once()
    mock_user_repository.create.assert_called_once()
    assert actual_result.id == expected_result.id


async def test_create_user_fail_duplicate_account_id(
    user_service,
    mock_user_repository,
    mock_session,
    mock_compensation_manager,
):
    # given
    mock_user_repository.exists_by_account_id.return_value = True

    # when & then
    with pytest.raises(UserAccountIdDuplicateException):
        await user_service.create_user(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            account_id=random_string(),
            name=random_string(),
            password=random_string(),
        )
    mock_user_repository.exists_by_account_id.assert_called_once()


async def test_update_user_info_success(
    user_service,
    mock_user_repository,
    mock_session,
):
    # given
    user_id: int = random_int()
    user: User = create_user(user_id=user_id)
    new_name: str = random_string()
    mock_user_repository.find_by_id.return_value = user

    # when
    result: User = await user_service.update_user_info(
        session=mock_session,
        request_user_id=user_id,
        user_id=user.id,
        name=new_name,
    )

    # then
    mock_user_repository.find_by_id.assert_called_once()
    assert result.name == new_name


async def test_update_user_info_fail_request_user_is_not_equal_to_target_user(
    user_service,
    mock_session,
):
    # given
    request_user_id: int = 1
    target_user_id: int = 2

    # when & then
    with pytest.raises(UserUpdatePermissionDeniedException):
        await user_service.update_user_info(
            session=mock_session,
            request_user_id=request_user_id,
            user_id=target_user_id,
            name=random_string(),
        )


async def test_update_user_info_fail_when_user_not_found(
    user_service,
    mock_user_repository,
    mock_session,
):
    # given
    user_id: int = random_int()
    mock_user_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(UserNotFoundException):
        await user_service.update_user_info(
            session=mock_session,
            request_user_id=user_id,
            user_id=user_id,
            name=random_string(),
        )
    mock_user_repository.find_by_id.assert_called_once()
