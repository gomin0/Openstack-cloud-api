import pytest

from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from domain.user.entitiy import User
from exception.project_exception import ProjectNotFoundException, ProjectAccessDeniedException, \
    UserRoleAlreadyInProjectException
from exception.user_exception import UserNotFoundException


async def test_find_projects(mock_session, mock_project_repository, project_service):
    # given
    name_like = "a"
    project1 = Project(id=1, name="Alpha", domain_id=1, openstack_id="1cd74dcf765544d79a8d5fb7db589133")
    project2 = Project(id=2, name="Beta", domain_id=1, openstack_id="50d30edec2af40fcba9c3e0783bb29ea")
    mock_project_repository.find_all.return_value = [project1, project2]

    # when
    result = await project_service.find_projects(
        session=mock_session,
        name_like=name_like,
        sort_by=ProjectSortOption.NAME,
        order=SortOrder.ASC,
        with_deleted=False,
        with_relations=True
    )

    # then
    assert result == [project1, project2]
    mock_project_repository.find_all.assert_called_once_with(
        session=mock_session,
        ids=None,
        name=None,
        name_like=name_like,
        sort_by=ProjectSortOption.NAME,
        order=SortOrder.ASC,
        with_deleted=False,
        with_relations=True
    )


async def test_get_project(mock_session, mock_project_repository, project_service):
    # given
    project_id = 1
    domain_id = 1
    project = Project(id=project_id, name="Test", domain_id=domain_id, openstack_id="1cd74dcf765544d79a8d5fb7db589133")

    mock_project_repository.find_by_id.return_value = project

    # when
    result = await project_service.get_project(
        session=mock_session,
        project_id=project_id,
        with_deleted=False,
        with_relations=True
    )

    # then
    assert result == project
    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        with_deleted=False,
        with_relations=True
    )


async def test_get_project_fail_not_found(mock_session, mock_project_repository, project_service):
    # given
    project_id = 999
    mock_project_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ProjectNotFoundException):
        await project_service.get_project(
            session=mock_session,
            project_id=project_id,
            with_deleted=False,
            with_relations=True
        )

    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        with_deleted=False,
        with_relations=True
    )


async def test_assign_user_success(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_user_repository,
    mock_project_user_repository,
    mock_keystone_client,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    user_id = 1
    project = Project(id=project_id, name="TestProject", openstack_id="pos", domain_id=1)
    user = User(id=user_id, name="target_user", openstack_id="uos", domain_id=1)

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_user_repository.find_by_id.return_value = user
    mock_project_user_repository.is_user_role_exist.return_value = False

    # when
    await project_service.assign_role_from_user_on_project(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        keystone_token="token",
        keystone_user_id=user_id,
        project_id=project_id,
        user_id=user_id
    )

    # then
    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id
    )
    mock_project_user_repository.exists_by_user_and_project.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        user_id=user_id
    )
    mock_user_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        user_id=user_id
    )
    mock_project_user_repository.is_user_role_exist.assert_called_once()
    mock_project_user_repository.add_user_role.assert_called_once()
    mock_keystone_client.assign_role_from_user_on_project.assert_called_once()


async def test_assign_user_fail_project_not_found(
    mock_session,
    mock_async_client,
    mock_project_repository,
    project_service,
    mock_compensation_manager
):
    # given
    mock_project_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ProjectNotFoundException):
        await project_service.assign_role_from_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            keystone_user_id=1,
            project_id=1,
            user_id=1
        )

    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=1
    )


async def test_assign_user_fail_access_denied(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    project = Project(id=project_id, name="TestProject", openstack_id="pos", domain_id=1)
    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = False

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await project_service.assign_role_from_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            keystone_user_id=1,
            project_id=project_id,
            user_id=1
        )

    mock_project_user_repository.exists_by_user_and_project.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        user_id=1
    )


async def test_assign_user_fail_user_not_found(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_user_repository,
    mock_project_user_repository,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    project = Project(id=project_id, name="TestProject", openstack_id="pos", domain_id=1)
    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_user_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(UserNotFoundException):
        await project_service.assign_role_from_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            keystone_user_id=1,
            project_id=project_id,
            user_id=1
        )

    mock_user_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        user_id=1
    )


async def test_assign_user_fail_already_assigned(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_user_repository,
    mock_project_user_repository,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    user_id = 1
    project = Project(id=project_id, name="TestProject", openstack_id="pos", domain_id=1)
    user = User(id=user_id, name="Target", openstack_id="uos", domain_id=1)

    mock_project_repository.find_by_id.return_value = project
    mock_user_repository.find_by_id.return_value = user
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_project_user_repository.is_user_role_exist.return_value = True

    # when & then
    with pytest.raises(UserRoleAlreadyInProjectException):
        await project_service.assign_role_from_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            keystone_user_id=1,
            project_id=project_id,
            user_id=user_id
        )

    mock_project_user_repository.is_user_role_exist.assert_called_once()
