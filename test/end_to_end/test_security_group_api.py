from unittest.mock import Mock

from common.domain.security_group.entity import ServerSecurityGroup
from test.util.database import add_to_db
from test.util.factory import create_domain, create_user, create_project, create_project_user, create_security_group, \
    create_server, create_access_token


async def test_find_security_groups_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))

    security_group1 = await add_to_db(db_session, create_security_group(project_id=project.id))
    security_group2 = await add_to_db(db_session, create_security_group(project_id=project.id))

    server = await add_to_db(db_session, create_server(project_id=project.id))
    await add_to_db(db_session, ServerSecurityGroup(server_id=server.id, security_group_id=security_group1.id))

    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()

        if method == "GET" and "/v2.0/security-group-rules" in url:
            mock_response.json.return_value = {"security_group_rules": []}

        else:
            raise ValueError("Unknown API endpoint")

        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.get(
        "/security-groups",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert "security_groups" in data
    assert len(data["security_groups"]) == 2


async def test_get_security_group_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))

    security_group = await add_to_db(db_session, create_security_group(project_id=project.id, name="security_group"))
    server = await add_to_db(db_session, create_server(project_id=project.id))
    await add_to_db(db_session, ServerSecurityGroup(server_id=server.id, security_group_id=security_group.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()

        if method == "GET" and "/v2.0/security-group-rules" in url:
            mock_response.json.return_value = {"security_group_rules": []}

        else:
            raise ValueError("Unknown API endpoint")

        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.get(
        f"/security-groups/{security_group.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == security_group.id
    assert data["name"] == "security_group"
    assert data["project_id"] == project.id


async def test_get_security_group_fail_not_found(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()

    security_group_id = 1

    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.get(
        f"/security-groups/{security_group_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "SECURITY_GROUP_NOT_FOUND"


async def test_get_security_group_fail_access_denied(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project1.id))
    security_group = await add_to_db(db_session, create_security_group(project_id=project2.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project1.id)

    # when
    response = await client.get(
        f"/security-groups/{security_group.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "SECURITY_GROUP_ACCESS_DENIED"


async def test_create_security_group_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "POST" and "/v2.0/security-groups" in url:
            mock_response.json.return_value = {
                "security_group": {
                    "id": "openstack-sg-id",
                    "name": "sg",
                    "description": "test",
                    "security_group_rules": []
                }
            }
        elif method == "POST" and "/v2.0/security-group-rules" in url:
            mock_response.json.return_value = {}
        elif method == "GET" and "/v2.0/security-group-rules" in url:
            mock_response.json.return_value = {"security_group_rules": []}
        else:
            raise ValueError(f"Unknown API endpoint")
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.post(
        "/security-groups",
        json={
            "name": "sg",
            "description": "test",
            "rules": [
                {
                    "protocol": "tcp",
                    "ether_type": "IPv4",
                    "direction": "ingress",
                    "port_range_min": 80,
                    "port_range_max": 80,
                    "remote_ip_prefix": "0.0.0.0/0"
                }
            ]
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "sg"
    assert data["project_id"] == project.id
    assert "rules" in data


async def test_create_security_group_fail_name_duplicated(client, db_session, mock_async_client):
    # given
    name = "same"
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await add_to_db(db_session, create_security_group(project_id=project.id, name=name))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.post(
        "/security-groups",
        json={
            "name": name,
            "description": "test",
            "rules": []
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "SECURITY_GROUP_NAME_DUPLICATED"


async def test_update_security_group_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))

    security_group = await add_to_db(
        db_session, create_security_group(project_id=project.id, name="old", description="desc")
    )
    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "GET" and "/security-group-rules" in url:
            mock_response.json.return_value = {
                "security_group_rules": [{
                    "id": "sgos",
                    "security_group_id": security_group.openstack_id,
                    "direction": "egress",
                    "ethertype": "IPv4",
                    "protocol": "tcp",
                    "port_range_min": 80,
                    "port_range_max": 80,
                    "remote_ip_prefix": "0.0.0.0/0"
                }]
            }
        elif method == "PUT" and "/v2.0/security-groups/" in url:
            mock_response.json.return_value = {}
        elif method == "DELETE" and "/v2.0/security-group-rules" in url:
            mock_response.json.return_value = {}
        elif method == "POST" and "/v2.0/security-group-rules" in url:
            mock_response.json.return_value = {
                "security_group_rules": [{
                    "id": "newsgos",
                    "security_group_id": security_group.openstack_id,
                    "direction": "egress",
                    "protocol": "tcp",
                    "ethertype": "IPv4",
                    "port_range_min": 80,
                    "port_range_max": 80,
                    "remote_ip_prefix": "0.0.0.0/0"
                }]
            }
        else:
            raise ValueError("Unknown API endpoint")

        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    # when
    response = await client.put(
        f"/security-groups/{security_group.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "new",
            "description": "new",
            "rules": [{
                "direction": "egress",
                "protocol": "tcp",
                "ether_type": "IPv4",
                "port_range_min": 22,
                "port_range_max": 22,
                "remote_ip_prefix": "0.0.0.0/0"
            }]
        }
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new"
    assert data["description"] == "new"


async def test_update_security_group_fail_not_found(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project.id)
    security_group_id = 1

    # when
    response = await client.put(
        f"/security-groups/{security_group_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "new",
            "description": "new-desc",
            "rules": []
        }
    )

    # then
    assert response.status_code == 404
    assert response.json()["code"] == "SECURITY_GROUP_NOT_FOUND"


async def test_update_security_group_fail_access_denied(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project1.id))
    security_group = await add_to_db(db_session, create_security_group(project_id=project2.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id, project_id=project1.id)

    # when
    response = await client.put(
        f"/security-groups/{security_group.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "new",
            "description": "desc",
            "rules": []
        }
    )

    # then
    assert response.status_code == 403
    assert response.json()["code"] == "SECURITY_GROUP_UPDATE_PERMISSION_DENIED"


async def test_update_security_group_fail_name_duplicated(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))

    security_group1 = await add_to_db(db_session, create_security_group(project_id=project.id, name="name"))
    security_group2 = await add_to_db(db_session, create_security_group(project_id=project.id, name="same"))

    await db_session.commit()
    access_token = create_access_token(user_id=user.id, project_id=project.id)

    # when
    response = await client.put(
        f"/security-groups/{security_group1.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "same",
            "description": "updated-desc",
            "rules": []
        }
    )

    # then
    assert response.status_code == 409
    assert response.json()["code"] == "SECURITY_GROUP_NAME_DUPLICATED"
