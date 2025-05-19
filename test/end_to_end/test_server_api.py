from unittest.mock import Mock

from httpx import Response, Request

from api_server.router.server.request import CreateServerRequest, CreateRootVolumeRequest
from common.application.server.service import ServerService
from common.domain.domain.entity import Domain
from common.domain.project.entity import Project
from common.domain.security_group.entity import SecurityGroup
from common.domain.server.entity import Server
from common.domain.server.enum import ServerStatus
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.server_exception import ServerNotFoundException, ServerUpdatePermissionDeniedException
from test.util.database import add_to_db
from test.util.factory import (
    create_domain, create_user, create_project, create_server, create_access_token, create_volume, create_security_group
)
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
            volume_id=1, project_id=project.id, server=server1, is_root_volume=True, image_openstack_id="123"
        )
    )
    await add_to_db(
        db_session, create_volume(
            volume_id=2, project_id=project.id, server=server2, is_root_volume=True, image_openstack_id="456"
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
            volume_id=1, project_id=project.id, server=server, is_root_volume=True, image_openstack_id="123"
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


async def test_create_server_success(mocker, client, db_session, mock_async_client, async_session_maker):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    security_group: SecurityGroup = await add_to_db(db_session, create_security_group(project_id=project.id))
    await db_session.commit()

    created_server_openstack_id: str = random_string(length=36)

    def request_side_effect(method, url, *args, **kwargs):
        if method == "POST" and "/v2.0/ports" in url:
            return Response(
                status_code=201,
                json={
                    "port": {

                        "id": random_string(length=36),
                        "name": random_string(),
                        "network_id": random_string(),
                        "project_id": project.openstack_id,
                        "status": "DOWN",
                        "fixed_ips": [
                            {"ip_address": "192.168.127.12"}
                        ],
                    },
                },
                request=Request(method=method, url=url),
            )
        if method == "POST" and "/v2.1/servers" in url:
            return Response(
                status_code=202,
                json={
                    "server": {"id": created_server_openstack_id},
                },
                request=Request(method=method, url=url),
            )
        if method == "GET" and "/v2.1/servers" in url:
            return Response(
                status_code=200,
                json={
                    "server": {
                        "id": created_server_openstack_id,
                        "tenant_id": project.openstack_id,
                        "status": "ACTIVE",
                        "os-extended-volumes:volumes_attached": [
                            {"id": random_string(length=36)},
                        ]
                    }
                },
                request=Request(method=method, url=url),
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = request_side_effect

    ServerService.CHECK_INTERVAL_SECONDS_FOR_SERVER_CREATION = 0

    request: CreateServerRequest = CreateServerRequest(
        name=random_string(),
        description=random_string(),
        flavor_id=random_string(length=36),
        network_id=random_string(length=36),
        root_volume=CreateRootVolumeRequest(
            size=random_int(),
            image_id=random_string(length=36),
        ),
        security_group_ids=[security_group.id]
    )

    # when
    access_token = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.post(
        url=f"/servers",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=request.model_dump(),
    )

    # then
    assert response.status_code == 202
    assert response.json()["openstack_id"] == created_server_openstack_id


async def test_create_server_fail_server_name_duplicated(
    mocker, client, db_session, mock_async_client, async_session_maker
):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server: Server = await add_to_db(db_session, create_server(project_id=project.id))
    await db_session.commit()

    request: CreateServerRequest = CreateServerRequest(
        name=server.name,
        description=random_string(),
        flavor_id=random_string(length=36),
        network_id=random_string(length=36),
        root_volume=CreateRootVolumeRequest(
            size=random_int(),
            image_id=random_string(length=36),
        ),
        security_group_ids=[random_int()]
    )

    # when
    access_token = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.post(
        url=f"/servers",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=request.model_dump(),
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "SERVER_NAME_DUPLICATE"


async def test_create_server_fail_security_group_access_denied(
    mocker, client, db_session, mock_async_client, async_session_maker
):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)

    project_id: int = random_int()
    requesting_project_id: int = random_int()

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(project_id=project_id, domain_id=domain.id))
    security_group: SecurityGroup = await add_to_db(db_session, create_security_group(project_id=project.id))
    await db_session.commit()

    request: CreateServerRequest = CreateServerRequest(
        name=random_string(),
        description=random_string(),
        flavor_id=random_string(length=36),
        network_id=random_string(length=36),
        root_volume=CreateRootVolumeRequest(
            size=random_int(),
            image_id=random_string(length=36),
        ),
        security_group_ids=[security_group.id]
    )

    # when
    access_token = create_access_token(project_id=requesting_project_id)
    response: Response = await client.post(
        url=f"/servers",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=request.model_dump(),
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "SECURITY_GROUP_ACCESS_DENIED"


async def test_attach_volume_to_server_success(client, db_session, mock_async_client, async_session_maker):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server: Server = await add_to_db(db_session, create_server(project_id=project.id))
    root_volume: Volume = await add_to_db(
        db_session,
        create_volume(
            volume_id=1,
            project_id=project.id,
            server_id=server.id,
            is_root_volume=True,
            image_openstack_id=random_string(length=36)
        )
    )
    volume: Volume = await add_to_db(db_session, create_volume(volume_id=2, project_id=project.id))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs) -> Response:
        if method == "POST" and f"/v2.1/servers/{server.openstack_id}/os-volume_attachments" in url:
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
                        "status": "in-use",
                        "size": 1
                    }
                },
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect

    ServerService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_ATTACHMENT = 0

    # when
    access_token = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.post(
        url=f"/servers/{server.id}/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    res_data: dict = response.json()
    assert response.status_code == 200
    assert res_data["id"] == server.id
    assert len(res_data["volumes"]) == 1


async def test_attach_volume_to_server_fail_when_volume_is_already_attached(
    client, db_session, mock_async_client, async_session_maker
):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server: Server = await add_to_db(db_session, create_server(project_id=project.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id, server_id=server.id,
                                                               status=VolumeStatus.IN_USE))
    await db_session.commit()

    # when
    access_token = create_access_token(project_id=project.id)
    response: Response = await client.post(
        url=f"/servers/{server.id}/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "VOLUME_ALREADY_ATTACHED"


async def test_delete_server_success(mocker, client, db_session, async_session_maker, mock_async_client):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    volume = await add_to_db(db_session, create_volume(project_id=project.id, server=server, is_root_volume=True))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs):
        if method == "DELETE" and f"/v2.1/servers/{server.openstack_id}" in url:
            return Response(
                status_code=204,
                request=Request(method=method, url=url)
            )
        elif method == "GET" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=404,
                request=Request(url=url, method=method)
            )
        elif method == "GET" and f"/v2.1/servers/{server.openstack_id}" in url:
            return Response(
                status_code=404,
                request=Request(url=url, method=method)
            )
        elif method == "DELETE" and f"/v2.0/ports/" in url:
            return Response(
                status_code=204,
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect
    access_token = create_access_token(
        user_id=user.id, project_id=project.id, project_openstack_id=project.openstack_id
    )

    # when
    response = await client.delete(
        f"/servers/{server.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 202


async def test_delete_server_fail_server_not_found(client, db_session, mock_async_client):
    # given
    server_id = 1
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.delete(
        f"/servers/{server_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "SERVER_NOT_FOUND"


async def test_start_server_success(mocker, client, db_session, async_session_maker, mock_async_client):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id, status=ServerStatus.SHUTOFF))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs):
        if method == "POST" and f"/v2.1/servers/{server.openstack_id}/action" in url:
            return Response(
                status_code=202,
                request=Request(method=method, url=url)
            )
        elif method == "GET" and f"/v2.1/servers/{server.openstack_id}" in url:
            return Response(
                status_code=200,
                json={
                    "server": {
                        "id": server.openstack_id,
                        "tenant_id": project.openstack_id,
                        "status": ServerStatus.ACTIVE.value,
                        "os-extended-volumes:volumes_attached": [
                            {"id": random_string(length=36)},
                        ]
                    }
                },
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect
    access_token = create_access_token(
        user_id=user.id, project_id=project.id, project_openstack_id=project.openstack_id
    )

    # when
    response = await client.put(
        f"/servers/{server.id}/status",
        params={"status": ServerStatus.ACTIVE.value},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 202


async def test_stop_server_success(mocker, client, db_session, async_session_maker, mock_async_client):
    # given
    mocker.patch("common.util.background_task_runner.get_async_client", return_value=mock_async_client)
    mocker.patch("common.util.background_task_runner.session_factory", new_callable=lambda: async_session_maker)
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id, status=ServerStatus.ACTIVE))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs):
        if method == "POST" and f"/v2.1/servers/{server.openstack_id}/action" in url:
            return Response(
                status_code=202,
                request=Request(method=method, url=url)
            )
        elif method == "GET" and f"/v2.1/servers/{server.openstack_id}" in url:
            return Response(
                status_code=200,
                json={
                    "server": {
                        "id": server.openstack_id,
                        "tenant_id": project.openstack_id,
                        "status": ServerStatus.SHUTOFF.value,
                        "os-extended-volumes:volumes_attached": [
                            {"id": random_string(length=36)},
                        ]
                    }
                },
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect
    access_token = create_access_token(
        user_id=user.id, project_id=project.id, project_openstack_id=project.openstack_id
    )

    # when
    response = await client.put(
        f"/servers/{server.id}/status",
        params={"status": ServerStatus.SHUTOFF.value},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 202


async def test_update_server_status_fail_not_found(client, db_session, mock_async_client):
    # given
    server_id = 1
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()

    access_token = create_access_token(
        user_id=user.id, project_id=project.id, project_openstack_id=project.openstack_id
    )

    # when
    response = await client.put(
        f"/servers/{server_id}/status",
        params={"status": ServerStatus.SHUTOFF.value},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "SERVER_NOT_FOUND"
