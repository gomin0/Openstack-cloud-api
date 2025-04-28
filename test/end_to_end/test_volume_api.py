from urllib.request import Request

from httpx import Response

from common.domain.domain.entity import Domain
from common.domain.project.entity import Project
from common.domain.volume.enum import VolumeStatus
from test.util.database import add_to_db
from test.util.factory import create_access_token, create_volume, create_project, create_domain
from test.util.random import random_string


async def test_create_volume_success(
    mocker,
    client,
    db_session,
    async_session_maker,
    mock_async_client
):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.AsyncSessionLocal", new_callable=lambda: async_session_maker)

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()

    created_volume_openstack_id: str = random_string(length=36)

    def mock_client_request_side_effect(method, url, *args, **kwargs):
        if method == "POST" and f"/v3/{project.openstack_id}/volumes" in url:
            return Response(
                status_code=201,
                json={"volume": {"id": created_volume_openstack_id}},
                request=Request(method=method, url=url)
            )
        elif method == "GET" and f"/v3/{project.openstack_id}/volumes/{created_volume_openstack_id}" in url:
            return Response(
                status_code=200,
                json={"volume": {"status": "available"}},
                request=Request(method=method, url=url)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect

    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)

    # when
    response: Response = await client.post(
        url="/volumes",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": "volume1",
            "description": "This volume is...",
            "size": 1,
            "volume_type_id": "64abcd22-a30b-4982-8f82-332e89ff4bf7",
            "image_id": "14abcd22-a30b-4982-8f82-332e89ff4bf7",
        }
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 202
    assert response_body["status"] == VolumeStatus.CREATING.value


async def test_create_volume_fail_when_name_already_exists(client, db_session):
    # given
    volume_name: str = random_string()
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_volume(project_id=project.id, name=volume_name))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.post(
        url="/volumes",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": volume_name,
            "description": "This volume is...",
            "size": 1,
            "volume_type_id": "64abcd22-a30b-4982-8f82-332e89ff4bf7",
        }
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 409
    assert response_body["code"] == "VOLUME_NAME_DUPLICATE"
