from domain.enum import SortOrder
from domain.user.entitiy import User
from domain.user.enum import UserSortOption


async def test_find_users(mock_session, mock_user_repository, user_service):
    # given
    account_id = "user1"
    user1 = User(openstack_id="user123", domain_id=1, account_id="user1", name="사용자1", password="@!#32")
    user2 = User(openstack_id="user1234", domain_id=1, account_id="user2", name="사용자1", password="@!#32")
    mock_user_repository.find_all.return_value = [user1, user2]

    # when
    result = await user_service.find_users(
        session=mock_session,
        account_id=account_id,
        sort_by=UserSortOption.ACCOUNT_ID,
        sort_order=SortOrder.ASC,
        with_relations=True
    )

    # then
    assert result == [user1, user2]
    mock_user_repository.find_all.assert_called_once_with(
        session=mock_session,
        user_id=None,
        account_id=account_id,
        name=None,
        sort_by=UserSortOption.ACCOUNT_ID,
        sort_order=SortOrder.ASC,
        with_relations=True
    )
