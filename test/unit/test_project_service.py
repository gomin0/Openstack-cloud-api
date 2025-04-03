import pytest

from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from exception.project_exception import ProjectNotFoundException


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
        with_relations=True
    )

    # then
    assert result == project
    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
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
            with_relations=True
        )

    mock_project_repository.find_by_id.assert_called_once_with(
        session=mock_session,
        project_id=project_id,
        with_relations=True
    )
