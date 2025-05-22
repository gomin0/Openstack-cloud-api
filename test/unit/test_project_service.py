from datetime import datetime, timezone
from unittest.mock import call

import pytest

from common.application.project.response import ProjectDetailResponse
from common.domain.domain.entity import Domain
from common.domain.enum import SortOrder
from common.domain.project.entity import Project, ProjectUser
from common.domain.project.enum import ProjectSortOption
from common.domain.user.entity import User
from common.exception.project_exception import (ProjectNotFoundException, ProjectNameDuplicatedException,
                                                ProjectAccessDeniedException, UserAlreadyInProjectException,
                                                UserNotInProjectException)
from common.exception.user_exception import UserNotFoundException
from common.util.envs import Envs, get_envs
from test.util.factory import create_project_stub

envs: Envs = get_envs()


async def test_find_projects(mock_session, mock_project_repository, project_service):
    # given
    name_like = "a"
    domain = Domain(
        id=1,
        name="domain",
        openstack_id="779b35a7173444e387a7f34134a56e31",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )

    project1 = create_project_stub(domain=domain, project_id=1)
    project2 = create_project_stub(domain=domain, project_id=2)

    mock_project_repository.find_all.return_value = [project1, project2]

    # when
    result = await project_service.find_projects_details(
        session=mock_session,
        name_like=name_like,
        sort_by=ProjectSortOption.NAME,
        order=SortOrder.ASC,
        with_deleted=False,
        with_relations=True
    )

    # then
    expected = [
        await ProjectDetailResponse.from_entity(project1),
        await ProjectDetailResponse.from_entity(project2),
    ]
    assert result.projects == expected

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
    domain = Domain(
        id=1,
        name="domain",
        openstack_id="779b35a7173444e387a7f34134a56e31",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    project = create_project_stub(domain=domain, project_id=project_id)

    mock_project_repository.find_by_id.return_value = project

    # when
    result = await project_service.get_project_detail(
        session=mock_session,
        project_id=project_id,
        with_deleted=False,
        with_relations=True
    )

    # then
    assert result == await ProjectDetailResponse.from_entity(project)
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
        await project_service.get_project_detail(
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
    new_name = "New"
    openstack_id = "abc123"
    domain = Domain(
        id=1,
        name="domain",
        openstack_id="779b35a7173444e387a7f34134a56e31",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    project = create_project_stub(domain=domain, openstack_id=openstack_id, project_id=project_id)

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_project_and_user.return_value = True
    mock_project_repository.exists_by_name.return_value = False
    mock_project_repository.update_with_optimistic_lock.return_value = project
    mock_keystone_client.update_project.return_value = None

    # when
    result = await project_service.update_project(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        user_id=user_id,
        project_id=project_id,
        new_name=new_name
    )

    # then
    assert result.name == new_name
    mock_project_repository.find_by_id.assert_called_once()
    mock_project_user_repository.exists_by_project_and_user.assert_called_once()
    mock_project_repository.exists_by_name.assert_called_once_with(session=mock_session, name=new_name)
    mock_project_repository.update_with_optimistic_lock.assert_called_once()
    mock_keystone_client.update_project.assert_called_once()


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
    mock_project_user_repository.exists_by_project_and_user.return_value = True
    mock_project_repository.exists_by_name.return_value = True

    # when & then
    with pytest.raises(ProjectNameDuplicatedException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            user_id=123,
            project_id=project_id,
            new_name=new_name
        )

    mock_project_repository.exists_by_name.assert_called_once_with(
        session=mock_session,
        name=new_name
    )
    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id
    )
    mock_project_user_repository.exists_by_project_and_user.assert_called_once_with(
        session=mock_session,
        user_id=123,
        project_id=project_id
    )


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
    mock_project_user_repository.exists_by_project_and_user.return_value = False

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await project_service.update_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            project_id=project_id,
            new_name=new_name,
            user_id=user_id
        )

    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
    )
    mock_project_user_repository.exists_by_project_and_user.assert_called_once_with(
        session=mock_session,
        user_id=user_id,
        project_id=project_id
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
    user1_id = 1
    user2_id = 2
    project = Project(id=project_id, name="TestProject", openstack_id="pos", domain_id=1)
    user1 = User(id=user1_id, name="u1", openstack_id="u1", domain_id=1)
    user2 = User(id=user2_id, name="u2", openstack_id="u2", domain_id=1)

    mock_project_repository.find_by_id.return_value = project
    mock_user_repository.find_by_id.return_value = user2
    mock_project_user_repository.exists_by_project_and_user.side_effect = [True, False]

    # when
    await project_service.assign_user_on_project(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        request_user_id=user1_id,
        project_id=project_id,
        user_id=user2_id
    )

    # then
    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id
    )
    mock_user_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        user_id=user2_id
    )
    mock_project_user_repository.exists_by_project_and_user.assert_has_calls([
        call(session=mock_session, project_id=project_id, user_id=user1_id),
        call(session=mock_session, project_id=project_id, user_id=user2_id)
    ])
    assert mock_project_user_repository.exists_by_project_and_user.call_count == 2

    mock_project_user_repository.create.assert_called_once()
    mock_keystone_client.assign_role_to_user_on_project.assert_called_once()


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
        await project_service.assign_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
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
    mock_project_user_repository.exists_by_project_and_user.return_value = False

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await project_service.assign_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
            project_id=project_id,
            user_id=1
        )

    mock_project_user_repository.exists_by_project_and_user.assert_called_once_with(
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
    mock_project_user_repository.exists_by_project_and_user.return_value = True
    mock_user_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(UserNotFoundException):
        await project_service.assign_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
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
    user1_id = 1
    user2_id = 2
    project = Project(id=project_id, name="TestProject", openstack_id="pos", domain_id=1)
    user = User(id=user1_id, name="u1", openstack_id="uos1", domain_id=1)
    user = User(id=user2_id, name="u2", openstack_id="uos2", domain_id=1)

    mock_project_repository.find_by_id.return_value = project
    mock_user_repository.find_by_id.return_value = user
    mock_project_user_repository.exists_by_project_and_user.side_effect = [True, True]

    # when & then
    with pytest.raises(UserAlreadyInProjectException):
        await project_service.assign_user_on_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=user1_id,
            project_id=project_id,
            user_id=user2_id
        )

    mock_project_user_repository.exists_by_project_and_user.assert_has_calls([
        call(session=mock_session, project_id=project_id, user_id=user1_id),
        call(session=mock_session, project_id=project_id, user_id=user2_id)
    ])
    assert mock_project_user_repository.exists_by_project_and_user.call_count == 2


async def test_unassign_user_success(
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
    project = Project(id=project_id, name="Project", openstack_id="pos", domain_id=1)
    user = User(id=user_id, name="User", openstack_id="uos", domain_id=1)
    project_user = ProjectUser(id=1, user_id=user_id, project_id=project_id)

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_project_and_user.return_value = True
    mock_user_repository.find_by_id.return_value = user
    mock_project_user_repository.find_by_project_and_user.return_value = project_user

    # when
    await project_service.unassign_user_from_project(
        compensating_tx=mock_compensation_manager,
        session=mock_session,
        client=mock_async_client,
        request_user_id=user_id,
        project_id=project_id,
        user_id=user_id
    )

    # then
    mock_project_repository.find_by_id.assert_called_once()
    mock_project_user_repository.exists_by_project_and_user.assert_called_once()
    mock_user_repository.find_by_id.assert_called_once()
    mock_project_user_repository.find_by_project_and_user.assert_called_once()


async def test_unassign_user_fail_project_not_found(
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
        await project_service.unassign_user_from_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
            project_id=1,
            user_id=1
        )

    mock_project_repository.find_by_id.assert_called_once()


async def test_unassign_user_fail_access_denied(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    project = Project(id=project_id, name="Project", openstack_id="pos", domain_id=1)
    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_project_and_user.return_value = False

    # when & then
    with pytest.raises(ProjectAccessDeniedException):
        await project_service.unassign_user_from_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
            project_id=project_id,
            user_id=1
        )

    mock_project_user_repository.exists_by_project_and_user.assert_called_once_with(
        session=mock_session,
        user_id=1,
        project_id=1
    )


async def test_unassign_user_fail_user_not_found(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    mock_user_repository,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    project = Project(id=project_id, name="Project", openstack_id="pos", domain_id=1)
    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_user_and_project.return_value = True
    mock_user_repository.find_by_id.return_value = None

    # when & then
    with pytest.raises(UserNotFoundException):
        await project_service.unassign_user_from_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
            project_id=project_id,
            user_id=1
        )
    mock_user_repository.find_by_id.assert_called_once_with(session=mock_session, user_id=1)


async def test_unassign_user_fail_user_not_in_project(
    mock_session,
    mock_async_client,
    mock_project_repository,
    mock_project_user_repository,
    mock_user_repository,
    project_service,
    mock_compensation_manager
):
    # given
    project_id = 1
    user_id = 1
    project = Project(id=project_id, name="Project", openstack_id="pos", domain_id=1)
    user = User(id=user_id, name="User", openstack_id="uos", domain_id=1)

    mock_project_repository.find_by_id.return_value = project
    mock_project_user_repository.exists_by_project_and_user.return_value = True
    mock_user_repository.find_by_id.return_value = user
    mock_project_user_repository.find_by_project_and_user.return_value = None

    # when & then
    with pytest.raises(UserNotInProjectException):
        await project_service.unassign_user_from_project(
            compensating_tx=mock_compensation_manager,
            session=mock_session,
            client=mock_async_client,
            request_user_id=1,
            project_id=project_id,
            user_id=user_id
        )

    mock_project_user_repository.find_by_project_and_user.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        user_id=user_id,
    )
