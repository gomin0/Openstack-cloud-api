import uuid
from datetime import datetime

import pytest

from domain.enum import EntityStatus
from domain.project.entity import Project
from test.conftest import test_client


async def create_project(session, name="Test Project"):
    project = Project(
        openstack_id=str(uuid.uuid4().hex),
        name=name,
        domain_id=1,
        status=EntityStatus.ACTIVE.value,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project


@pytest.mark.asyncio
async def test_get_projects(test_client, db_session):
    await create_project(db_session, "Project 1")
    await create_project(db_session, "Project 2")
    await create_project(db_session, "Project 3")

    response = test_client.get("/projects")

    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) >= 3
