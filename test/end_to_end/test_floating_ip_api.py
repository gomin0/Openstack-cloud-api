from unittest.mock import Mock

from common.util.envs import get_envs
from test.util.database import add_to_db
from test.util.factory import (
    create_domain,
    create_user,
    create_project,
    create_project_user,
    create_floating_ip,
    create_access_token,
    create_server, create_network_interface,
)

envs = get_envs()


async def test_find_floating_ips(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))

    floating_ip1 = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    floating_ip2 = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    await db_session.commit()

    token = create_access_token(
        user_id=user.id,
        user_openstack_id=user.openstack_id,
        project_id=project.id,
        project_openstack_id=project.openstack_id,
    )

    # when
    response = await client.get(
        "/floating-ips",
        headers={"Authorization": f"Bearer {token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert "floating_ips" in data
    assert len(data["floating_ips"]) == 2


async def test_get_floating_ip_success(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    await db_session.commit()

    token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        f"/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == floating_ip.id


async def test_get_floating_ip_not_found(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=user.domain_id))
    await db_session.commit()

    token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        "/floating-ips/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    # then
    assert response.status_code == 404


async def test_get_floating_ip_access_denied(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=user.domain_id))
    project2 = await add_to_db(db_session, create_project(domain_id=user.domain_id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project1.id))
    await db_session.commit()

    token = create_access_token(
        user_id=user.id,
        project_id=project2.id,
    )

    # when
    response = await client.get(
        f"/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # then
    assert response.status_code == 403


async def test_create_floating_ip_success(client, db_session, mock_async_client):
    # given
    floating_network_id = 'abcdefgh-1111-1111-1111-abcdef111111'
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "POST" and "/v2.0/floatingips" in url:
            mock_response.headers = {"x-subject-token": "keystone-token"}
            mock_response.json.return_value = {
                "floatingip": {
                    "id": "fios",
                    "status": "DOWN",
                    "floating_ip_address": "10.0.0.1"
                }
            }
        else:
            raise ValueError("Unknown API endpoint")
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.post(
        "/floating-ips",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"floating_network_id": floating_network_id}
    )

    # then
    assert response.status_code == 201
    data = response.json()
    assert data["address"] == "10.0.0.1"


async def test_delete_floating_ip_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "DELETE" and "/v2.0/floatingips" in url:
            mock_response.status_code = 204
            mock_response.raise_for_status.return_value = None
        else:
            raise ValueError("Unknown API endpoint")
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.delete(
        f"/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 204


async def test_delete_floating_ip_fail_not_found(client, db_session, mock_async_client):
    # given
    floating_ip_id = 1
    access_token = create_access_token(user_id=1, project_id=1)

    # when
    response = await client.delete(
        f"/floating-ips/{floating_ip_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "FLOATING_IP_NOT_FOUND"


async def test_delete_floating_ip_fail_permission_denied(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project2.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project1.id)

    # when
    response = await client.delete(
        f"/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "FLOATING_IP_DELETE_PERMISSION_DENIED"


async def test_delete_floating_ip_fail_server_attached(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    network_interface = await add_to_db(db_session, create_network_interface(server_id=server.id))
    floating_ip = await add_to_db(
        db_session,
        create_floating_ip(project_id=project.id, network_interface_id=network_interface.id)
    )
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.delete(
        f"/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "ATTACHED_FLOATING_IP_DELETION"
