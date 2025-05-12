from test.util.database import add_to_db
from test.util.factory import create_domain, create_user, create_project, create_server, create_access_token, \
    create_volume


async def test_find_servers_success(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    server1 = await add_to_db(db_session, create_server(project_id=project.id))
    server2 = await add_to_db(db_session, create_server(project_id=project.id))
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
    assert response.json()["code"] == "SERVER_ACCESS_DENIED"
