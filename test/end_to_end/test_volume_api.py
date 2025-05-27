from httpx import Response, Request

from common.application.volume.service import VolumeService
from common.domain.domain.entity import Domain
from common.domain.project.entity import Project
from common.domain.server.entity import Server
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.exception.volume_exception import VolumeAccessPermissionDeniedException, VolumeNotFoundException
from test.util.database import add_to_db
from test.util.factory import create_access_token, create_volume, create_project, create_domain, create_server
from test.util.random import random_string, random_int


async def test_find_volume_details_success(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_volume(volume_id=1, project_id=project.id))
    await add_to_db(db_session, create_volume(volume_id=2, project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.get(
        url="/volumes",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 200
    assert len(response.json()["volumes"]) == 2


async def test_get_volume_detail_success(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.get(
        url=f"/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 200
    assert response.json()["id"] == volume.id


async def test_get_volume_detail_fail_not_found(client, db_session):
    # given

    # when
    access_token: str = create_access_token(project_id=random_int())
    response: Response = await client.get(
        url=f"/volumes/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == VolumeNotFoundException().code


async def test_get_volume_detail_fail_requester_do_not_have_access_permission(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(project_id=1, domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=2)
    response: Response = await client.get(
        url=f"/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == VolumeAccessPermissionDeniedException().code


async def test_create_volume_success(
    client,
    db_session,
    async_session_maker,
    mock_async_client
):
    # given
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


async def test_update_volume_info_success(client, db_session):
    # given
    new_name: str = random_string()
    new_description: str = random_string()
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.put(
        url=f"/volumes/{volume.id}/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": new_name,
            "description": new_description,
        }
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 200
    assert response_body["name"] == new_name
    assert response_body["description"] == new_description


async def test_update_volume_info_fail_volume_not_found(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.put(
        url=f"/volumes/1/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": random_string(),
            "description": random_string(),
        }
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 404
    assert response_body["code"] == "VOLUME_NOT_FOUND"


async def test_update_volume_info_fail_when_has_not_permission_to_update_volume(client, db_session):
    # given
    project_id: int = 1
    requesting_project_id: int = 2
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(project_id=project_id, domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=requesting_project_id)
    response: Response = await client.put(
        url=f"/volumes/{volume.id}/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": random_string(),
            "description": random_string(),
        }
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 403
    assert response_body["code"] == "VOLUME_UPDATE_PERMISSION_DENIED"


async def test_update_volume_info_fail_when_new_name_is_already_exists(client, db_session):
    # given
    new_name: str = random_string()
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_volume(volume_id=1, project_id=project.id, name=new_name))
    volume: Volume = await add_to_db(db_session, create_volume(volume_id=2, project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.put(
        url=f"/volumes/{volume.id}/info",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "name": new_name,
            "description": random_string(),
        }
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 409
    assert response_body["code"] == "VOLUME_NAME_DUPLICATE"


async def test_update_volume_size_success(client, db_session, mock_async_client):
    # given
    VolumeService.CHECK_INTERVAL_SECONDS_FOR_VOLUME_RESIZING = 0
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id, size=1))
    await db_session.commit()

    new_size: int = volume.size + 1

    def mock_client_request_side_effect(method, url, *args, **kwargs) -> Response:
        if method == "POST" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}/action" in url:
            return Response(
                status_code=202,
                request=Request(url=url, method=method)
            )
        elif method == "GET" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=200,
                json={
                    "volume": {
                        "id": volume.openstack_id,
                        "volume_type": "DEFAULT",
                        "status": "AVAILABLE",
                        "size": new_size
                    }
                },
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.put(
        url=f"/volumes/{volume.id}/size",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={"size": new_size}
    )

    # then
    response_body: dict = response.json()
    assert response.status_code == 200
    assert response_body["size"] == new_size


async def test_update_volume_size_fail_volume_not_found(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.put(
        url="/volumes/1/size",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={"size": 4}
    )

    # then
    assert response.status_code == 404


async def test_update_volume_size_fail_when_volume_status_is_not_available(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(
        db_session,
        create_volume(project_id=project.id, status=VolumeStatus.IN_USE, size=1)
    )
    await db_session.commit()

    new_size: int = volume.size + 1

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.put(
        url=f"/volumes/{volume.id}/size",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={"size": new_size}
    )

    # then
    assert response.status_code == 409


async def test_update_volume_size_fail_when_given_invalid_size(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id, size=1))
    await db_session.commit()

    new_size: int = volume.size

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.put(
        url=f"/volumes/{volume.id}/size",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={"size": new_size}
    )

    # then
    assert response.status_code == 400


async def test_delete_volume_success(client, db_session, mock_async_client):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs) -> Response:
        if method == "DELETE" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=204,
                request=Request(url=url, method=method)
            )
        elif method == "GET" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=404,
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.delete(
        url=f"/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 204


async def test_delete_volume_fail_volume_not_found(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id, project_openstack_id=project.openstack_id)
    response: Response = await client.delete(
        url=f"/volumes/{random_int()}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json().get("code") == "VOLUME_NOT_FOUND"


async def test_delete_volume_fail_when_has_not_permission_to_delete_volume(client, db_session):
    # given
    project_id: int = 1
    requesting_project_id: int = 2
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(project_id=project_id, domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=requesting_project_id)
    response: Response = await client.delete(
        url=f"/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    assert response.json().get("code") == "VOLUME_DELETE_PERMISSION_DENIED"


async def test_delete_volume_fail_volume_is_linked_to_server(client, db_session, mock_async_client):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server: Server = await add_to_db(db_session, create_server(project_id=project.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id, server=server))
    await db_session.commit()

    def mock_client_request_side_effect(method, url, *args, **kwargs) -> Response:
        if method == "GET" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=404,
                request=Request(url=url, method=method)
            )
        if method == "DELETE" and f"/v3/{project.openstack_id}/volumes/{volume.openstack_id}" in url:
            return Response(
                status_code=204,
                request=Request(url=url, method=method)
            )
        raise ValueError("Unknown API endpoint")

    mock_async_client.request.side_effect = mock_client_request_side_effect

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.delete(
        url=f"/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    assert response.json().get("code") == "ATTACHED_VOLUME_DELETION"


async def test_delete_volume_fail_volume_status_is_not_deletable(client, db_session):
    # given
    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    volume: Volume = await add_to_db(db_session, create_volume(project_id=project.id, status=VolumeStatus.CREATING))
    await db_session.commit()

    # when
    access_token: str = create_access_token(project_id=project.id)
    response: Response = await client.delete(
        url=f"/volumes/{volume.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    assert response.json().get("code") == "VOLUME_STATUS_INVALID_FOR_DELETION"
