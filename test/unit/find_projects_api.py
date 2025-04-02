from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.project_service import ProjectService
from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption


@pytest.mark.asyncio
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
