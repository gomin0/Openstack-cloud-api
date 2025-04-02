from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.project_service import ProjectService
from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from exception.project_exception import ProjectNotFoundException


async def test_find_projects():
    # given
    session = AsyncMock(spec=AsyncSession)
    session.begin = AsyncMock()
    repository = AsyncMock()
    project1 = Project(id=1, name="Alpha", domain_id=1, openstack_id="1cd74dcf765544d79a8d5fb7db589133")
    project2 = Project(id=2, name="Beta", domain_id=1, openstack_id="50d30edec2af40fcba9c3e0783bb29ea")
    repository.find_all.return_value = [project1, project2]

    service = ProjectService(project_repository=repository)

    # when
    result = await service.find_projects(
        session=session,
        name_like="a",
        sort_by=ProjectSortOption.NAME,
        order=SortOrder.ASC
    )

    # then
    assert result == [project1, project2]
    repository.find_all.assert_called_once()


async def test_get_project():
    # given
    session = AsyncMock(spec=AsyncSession)
    session.begin = AsyncMock()
    repository = AsyncMock()
    project = Project(id=1, name="Test", domain_id=1, openstack_id="1cd74dcf765544d79a8d5fb7db589133")

    repository.find_by_id.return_value = project

    service = ProjectService(project_repository=repository)

    # when
    result = await service.get_project(session=session, project_id=1)

    # then
    assert result == project
    repository.find_by_id.assert_called_once_with(
        session=session,
        project_id=1,
        with_relations=False
    )


async def test_get_project_not_found():
    # given
    session = AsyncMock(spec=AsyncSession)
    session.begin = AsyncMock()
    repository = AsyncMock()
    repository.find_by_id.return_value = None

    service = ProjectService(project_repository=repository)

    # when & then
    with pytest.raises(ProjectNotFoundException):
        await service.get_project(session=session, project_id=999)
