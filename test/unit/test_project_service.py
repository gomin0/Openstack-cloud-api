import pytest

from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from exception.openstack_exception import OpenStackException
from exception.project_exception import ProjectNotFoundException, ProjectNameDuplicatedException, \
    ProjectAccessDeniedException


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


async def test_update_project(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    project_service,
    mock_keystone_client,
    mock_compensation_manager,
):
    # given
    project_id = 1
    user_id = 1
    domain_id = 1
    old_name = "Old"
    new_name = "New"
    token = "test_token"
    openstack_id = "abc123"

    project = Project(id=project_id, name=old_name, openstack_id=openstack_id, domain_id=domain_id)

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_project_repository.exists_by_name.return_value = False
    mock_project_repository.update_with_optimistic_lock.return_value = project

    # when
    result = await project_service.update_project(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        keystone_token=token,
        user_id=user_id,
        project_id=project_id,
        new_name=new_name
    )

    # then
    assert result.name == new_name
    mock_project_repository.find_by_id.assert_called_once()
    mock_project_repository.exists_by_name.assert_called_once_with(session=mock_session, name=new_name)
    mock_project_repository.update_with_optimistic_lock.assert_called_once()
    mock_keystone_client.update_project.assert_called_once_with(
        client=mock_async_client,
        project_openstack_id=openstack_id,
        name=new_name,
        keystone_token=token
    )


async def test_update_project_fail_not_found(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_keystone_client,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 999
    new_name = "New"
    mock_project_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(ProjectNotFoundException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            user_id=1,
            project_id=project_id,
            new_name=new_name
        )

    mock_project_repository.find_by_id.assert_called_once()


async def test_update_project_fail_duplicate_name(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    mock_keystone_client,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    new_name = "New"
    project = Project(id=project_id, name="Old", domain_id=1, openstack_id="abc")

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_project_repository.exists_by_name.return_value = True

    # when & then
    with pytest.raises(ProjectNameDuplicatedException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            user_id=123,
            project_id=project_id,
            new_name=new_name
        )

    mock_project_repository.exists_by_name.assert_called_once_with(session=mock_session, name=new_name)


async def test_update_project_fail_access_denied(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    project_service,
    mock_keystone_client,
    mock_compensation_manager,
):
    # given
    project_id = 1
    new_name = "New"
    user_id = 1
    project = Project(id=project_id, name="Old", domain_id=1, openstack_id="abc")

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = False

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            project_id=project_id,
            new_name=new_name,
            user_id=user_id
        )


async def test_update_project_fail_openstack_403(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    project_service,
    mock_keystone_client,
    mock_compensation_manager,
):
    # given
    project = Project(id=1, name="Old", domain_id=1, openstack_id="abc")
    new_name = "New"
    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_project_repository.exists_by_name.return_value = False
    mock_project_repository.update_with_optimistic_lock.return_value = project
    mock_keystone_client.update_project.side_effect = OpenStackException(openstack_status_code=403)

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            user_id=1,
            project_id=1,
            new_name=new_name
        )


async def test_update_project_fail_openstack_409(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    project_service,
    mock_keystone_client,
    mock_compensation_manager
):
    # given
    project = Project(id=1, name="Old", domain_id=1, openstack_id="abc")
    new_name = "New"
    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_project_repository.exists_by_name.return_value = False
    mock_project_repository.update_with_optimistic_lock.return_value = project
    mock_keystone_client.update_project.side_effect = OpenStackException(openstack_status_code=409)

    # when & then
    with pytest.raises(ProjectNameDuplicatedException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            keystone_token="token",
            user_id=1,
            project_id=1,
            new_name=new_name
        )
