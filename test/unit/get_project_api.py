from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.project_service import ProjectService
from domain.project.entity import Project
from exception.project_exception import ProjectNotFoundException


@pytest.mark.asyncio
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
    repository.find_by_id.assert_called_once_with(session, 1, joined=True)


@pytest.mark.asyncio
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
