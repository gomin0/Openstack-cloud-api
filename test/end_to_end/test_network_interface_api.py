from unittest.mock import Mock

from test.util.database import add_to_db
from test.util.factory import create_domain, create_user, create_project, create_server, create_floating_ip, \
    create_network_interface, create_access_token


async def test_attach_floating_ip_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    network_interface = await add_to_db(
        db_session,
        create_network_interface(server_id=server.id, project_id=project.id)
    )
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "PUT" and "/v2.0/floatingips/".format(floating_ip.openstack_id) in url:
            mock_response.status_code = 200
        else:
            raise ValueError("Unknown API endpoint")
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.post(
        f"/network-interfaces/{network_interface.id}/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 204


async def test_attach_floating_ip_fail_network_interface_not_found(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    network_interface_id = 1
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    await db_session.commit()

    access_token = create_access_token(user_id=1, project_id=project.id)

    # when
    response = await client.post(
        f"/network-interfaces/{network_interface_id}/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "NETWORK_INTERFACE_NOT_FOUND"


async def test_attach_floating_ip_fail_access_denied(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(project_id=1, domain_id=domain.id))
    project2 = await add_to_db(db_session, create_project(project_id=2, domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project1.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project1.id))
    network_interface = await add_to_db(
        db_session,
        create_network_interface(server_id=server.id, project_id=project2.id)
    )
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project1.id)

    # when
    response = await client.post(
        f"/network-interfaces/{network_interface.id}/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "NETWORK_INTERFACE_ACCESS_PERMISSION_DENIED"


async def test_attach_floating_ip_to_server_fail_floating_ip_not_found(client, db_session):
    # given
    floating_ip_id = 1
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    network_interface = await add_to_db(
        db_session,
        create_network_interface(server_id=server.id, project_id=project.id)
    )
    await db_session.commit()
    access_token = create_access_token(user_id=1, project_id=project.id)

    # when
    response = await client.post(
        f"/network-interfaces/{network_interface.id}/floating-ips/{floating_ip_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "FLOATING_IP_NOT_FOUND"


async def test_attach_floating_ip_fail_already_attached(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    network_interface = await add_to_db(
        db_session,
        create_network_interface(server_id=server.id, project_id=project.id)
    )
    floating_ip = await add_to_db(
        db_session, create_floating_ip(project_id=project.id, network_interface_id=network_interface.id)
    )
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.post(
        f"/network-interfaces/{network_interface.id}/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "FLOATING_IP_ALREADY_ATTACHED_TO_NETWORK_INTERFACE"


async def test_detach_floating_ip_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))

    server = await add_to_db(db_session, create_server(project_id=project.id))
    network_interface = await add_to_db(
        db_session,
        create_network_interface(server_id=server.id, project_id=project.id)
    )
    floating_ip = await add_to_db(
        db_session,
        create_floating_ip(
            project_id=project.id,
            network_interface_id=network_interface.id
        )
    )
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "PUT" and "/v2.0/floatingips/".format(floating_ip.openstack_id) in url:
            mock_response.status_code = 200
        else:
            raise ValueError("Unknown API endpoint")
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.delete(
        f"/network-interfaces/{network_interface.id}/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 204


async def test_detach_floating_ip_fail_floating_ip_not_found(client, db_session):
    # given
    network_interface_id = 1
    floating_ip_id = 1
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await db_session.commit()
    access_token = create_access_token(user_id=1, project_id=project.id)

    # when
    response = await client.delete(
        f"/network-interfaces/{network_interface_id}/floating-ips/{floating_ip_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "FLOATING_IP_NOT_FOUND"


async def test_detach_floating_ip_fail_not_attached(client, db_session):
    # given
    network_interface_id = 1
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    floating_ip = await add_to_db(db_session, create_floating_ip(project_id=project.id))
    await db_session.commit()

    access_token = create_access_token(user_id=1, project_id=project.id)

    # when
    response = await client.delete(
        f"/network-interfaces/{network_interface_id}/floating-ips/{floating_ip.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "FLOATING_IP_NOT_ATTACHED_TO_NETWORK_INTERFACE"
