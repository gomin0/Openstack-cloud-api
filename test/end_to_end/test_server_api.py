from unittest.mock import Mock

from httpx import Response, Request

from common.domain.domain.entity import Domain
from common.domain.project.entity import Project
from common.domain.server.entity import Server
from common.domain.volume.enum import VolumeStatus
from common.exception.server_exception import ServerNotFoundException, ServerUpdatePermissionDeniedException
from test.util.database import add_to_db
from test.util.factory import create_domain, create_user, create_project, create_server, create_access_token, \
    create_volume
from test.util.random import random_string, random_int


async def test_find_servers_success(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server1 = await add_to_db(db_session, create_server(server_id=1, project_id=project.id))
    server2 = await add_to_db(db_session, create_server(server_id=2, project_id=project.id))
    await add_to_db(
        db_session, create_volume(
            volume_id=1, project_id=project.id, server_id=server1.id, is_root_volume=True, image_openstack_id="123"
        )
    )
    await add_to_db(
        db_session, create_volume(
            volume_id=2, project_id=project.id, server_id=server2.id, is_root_volume=True, image_openstack_id="456"
        )
    )
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        "/servers",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert len(data["servers"]) == 2


async def test_get_server_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    await add_to_db(
        db_session, create_volume(
            volume_id=1, project_id=project.id, server_id=server.id, is_root_volume=True, image_openstack_id="123"
        )
    )
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        f"/servers/{server.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == server.id


async def test_get_server_fail_not_found(client, db_session):
    # given
    server_id = 1
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        f"/servers/{server_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "SERVER_NOT_FOUND"


async def test_get_server_fail_access_denied(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(server_id=1, project_id=project2.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project1.id)

    # when
    response = await client.get(
        f"/servers/{server.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "SERVER_ACCESS_PERMISSION_DENIED"


async def test_update_server_info_success(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server: Server = await add_to_db(db_session, create_server(project_id=project.id))
    await db_session.commit()

    new_name: str = random_string()
    new_description: str = random_string()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.put(
        url=f"/servers/{server.id}/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": new_name,
            "description": new_description,
        },
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 200
    assert response_body["name"] == new_name
    assert response_body["description"] == new_description


async def test_update_server_info_fail_server_not_found(client, db_session):
    # given
    new_name: str = random_string()
    new_description: str = random_string()

    # when
    access_token: str = create_access_token(project_id=random_int())
    response: Response = await client.put(
        url="/servers/1/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": new_name,
            "description": new_description,
        },
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == ServerNotFoundException().code


async def test_update_server_info_fail_when_requester_has_not_update_permission(client, db_session):
    # given
    project_id: int = 1
    requesting_project_id: int = 2

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(project_id=project_id, domain_id=domain.id))
    server: Server = await add_to_db(db_session, create_server(project_id=project.id))
    await db_session.commit()

    new_name: str = random_string()
    new_description: str = random_string()

    # when
    access_token: str = create_access_token(project_id=requesting_project_id)
    response: Response = await client.put(
        url=f"/servers/{server.id}/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": new_name,
            "description": new_description,
        },
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == ServerUpdatePermissionDeniedException().code


async def test_update_server_info_fail_new_name_is_duplicated(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server1: Server = await add_to_db(db_session, create_server(server_id=1, project_id=project.id, name="server1"))
    server2: Server = await add_to_db(db_session, create_server(server_id=2, project_id=project.id, name="server2"))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.put(
        url=f"/servers/{server1.id}/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": server2.name,
            "description": server1.description,
        },
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "SERVER_NAME_DUPLICATE"


async def test_get_server_vnc_url_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)
    vnc_url = "vnc-url"

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "POST" and "/v2.1/servers/{}/action".format(server.openstack_id) in url:
            mock_response.json.return_value = {"console": {"url": vnc_url}}
        else:
            raise ValueError("Unknown API endpoint")
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.get(
        f"/servers/{server.id}/vnc-url",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert data["url"] == vnc_url


async def test_get_server_vnc_url_fail_not_found(client, db_session):
    # given
    server_id = 1
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        f"/servers/{server.id}/vnc-url",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "SERVER_NOT_FOUND"


async def test_get_server_vnc_url_fail_access_denied(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(server_id=1, project_id=project2.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project1.id)

    # when
    response = await client.get(
        f"/servers/{server.id}/vnc-url",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "SERVER_ACCESS_PERMISSION_DENIED"


async def test_detach_volume_from_server_success(client, db_session, mock_async_client, async_session_maker):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    root_volume = await add_to_db(
        db_session,
        create_volume(
            volume_id=1,
            openstack_id=random_string(),
            project_id=project.id,
            image_openstack_id=random_string(),
            server_id=server.id,
            is_root_volume=True,
            status=VolumeStatus.IN_USE,
        )
    )
    volume = await add_to_db(db_session, create_volume(
        volume_id=2, project_id=project.id, is_root_volume=False, server_id=server.id, status=VolumeStatus.IN_USE
    ))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs) -> Response:
        if method == "DELETE" and f"/v2.1/servers/{server.openstack_id}/os-volume_attachments/{volume.openstack_id}" in url:
            return Response(
                status_code=200,
                request=Request(url=url, method=method)
            )
        if method == "GET" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=200,
                json={
                    "volume": {
                        "id": volume.openstack_id,
                        "volume_type": "DEFAULT",
                        "status": "available",
                        "size": 1
                    }
                },
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect
    access_token = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)

    # when
    response = await client.delete(
        url=f"/servers/{server.id}/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200


async def test_detach_volume_from_server_fail_volume_not_attached(
    client, db_session, mock_async_client, async_session_maker
):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    root_volume = await add_to_db(
        db_session,
        create_volume(
            volume_id=1,
            openstack_id=random_string(),
            project_id=project.id,
            server_id=server.id,
            is_root_volume=True,
            image_openstack_id=random_string(length=36)
        )
    )
    volume = await add_to_db(
        db_session,
        create_volume(volume_id=2, project_id=project.id, is_root_volume=False, server_id=server.id)
    )
    await db_session.commit()

    access_token = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)

    # when
    response = await client.delete(
        url=f"/servers/{server.id}/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409


async def test_detach_volume_from_server_fail_cannot_detach_root_volume(
    client, db_session, mock_async_client, async_session_maker):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    root_volume = await add_to_db(
        db_session,
        create_volume(
            volume_id=1,
            project_id=project.id,
            server_id=server.id,
            is_root_volume=True,
            image_openstack_id=random_string(length=36)
        )
    )
    await db_session.commit()

    access_token = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)

    # when
    response = await client.delete(
        url=f"/servers/{server.id}/volumes/{root_volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
