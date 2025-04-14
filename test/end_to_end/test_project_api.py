from common.envs import Envs, get_envs
from test.util.database import add_to_db
from test.util.factory import create_domain, create_user, create_project, create_project_user, create_access_token

envs: Envs = get_envs()


async def test_find_projects(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user1 = await add_to_db(db_session, create_user(domain_id=domain.id))
    user2 = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트1"))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id))
    project_user1 = await add_to_db(db_session, create_project_user(user_id=user1.id, project_id=project1.id))
    project_user2 = await add_to_db(db_session, create_project_user(user_id=user1.id, project_id=project1.id))
    await db_session.commit()

    # when
    response = await client.get("/projects")

    # then
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert len(data["projects"]) == 2

    project_data = None
    for p in data["projects"]:
        if p["name"] == "프로젝트1":
            project_data = p
            break
    assert len(project_data["accounts"]) == 2


async def test_find_projects_with_name_like(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user1 = await add_to_db(db_session, create_user(domain_id=domain.id))
    user2 = await add_to_db(db_session, create_user(domain_id=domain.id))
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트1"))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트2"))
    project_user1 = await add_to_db(db_session, create_project_user(user_id=user1.id, project_id=project1.id))
    project_user2 = await add_to_db(db_session, create_project_user(user_id=user1.id, project_id=project2.id))
    await db_session.commit()

    # when
    response = await client.get("/projects?name_like=2")

    # then
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 1
    assert data["projects"][0]["name"] == "프로젝트2"


async def test_get_project(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain(name="도메인"))
    user = await add_to_db(db_session, create_user(domain_id=domain.id, name="ted"))
    project = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트"))
    project_user = await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()

    # when
    response = await client.get(f"/projects/{project.id}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == "프로젝트"
    assert data["domain"]["id"] == domain.id
    assert data["domain"]["name"] == "도메인"
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["name"] == "ted"


async def test_get_project_fail_not_found(client):
    # given
    project_id = 999999

    # when
    response = await client.get(f"/projects/{project_id}")

    # then
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PROJECT_NOT_FOUND"


async def test_update_project(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트1"))
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project_user = await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id)

    # when
    response = await client.put(
        f"/projects/{project.id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == "New Name"


async def test_update_project_fail_not_found(client, db_session):
    # given
    project_id = 999999

    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id)

    # when
    response = await client.put(
        f"/projects/{project_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PROJECT_NOT_FOUND"


async def test_update_project_fail_name_duplicated(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    project1 = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트1"))
    project2 = await add_to_db(db_session, create_project(domain_id=domain.id, name="프로젝트2"))
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project_user = await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project1.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id)

    # when
    response = await client.put(
        f"/projects/{project1.id}",
        json={"name": project2.name},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "PROJECT_NAME_DUPLICATED"


async def test_update_project_fail_access_denied(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    await db_session.commit()
    access_token = create_access_token(user_id=user.id)

    # when
    response = await client.put(
        f"/projects/{project.id}",
        json={"name": "New Project Name"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "PROJECT_ACCESS_DENIED"


async def test_assign_user_to_project(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user1 = await add_to_db(db_session, create_user(domain_id=domain.id))
    user2 = await add_to_db(db_session, create_user(domain_id=domain.id))
    project_user = await add_to_db(db_session, create_project_user(user_id=user1.id, project_id=project.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user1.id)

    # when
    response = await client.post(
        f"/projects/{project.id}/users/{user2.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 204


async def test_assign_user_to_project_fail_project_not_found(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user.id)
    project_id = 1

    # when
    response = await client.post(
        f"/projects/{project_id}/users/{user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PROJECT_NOT_FOUND"


async def test_assign_user_to_project_fail_access_denied(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user1 = await add_to_db(db_session, create_user(domain_id=domain.id))
    user2 = await add_to_db(db_session, create_user(domain_id=domain.id))
    await db_session.commit()

    access_token = create_access_token(user_id=user1.id)

    # when
    response = await client.post(
        f"/projects/{project.id}/users/{user2.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "PROJECT_ACCESS_DENIED"


async def test_assign_user_to_project_fail_already_assigned(client, db_session):
    # given
    domain = await add_to_db(db_session, create_domain())
    project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user1 = await add_to_db(db_session, create_user(domain_id=domain.id))
    user2 = await add_to_db(db_session, create_user(domain_id=domain.id))
    project_user1 = await add_to_db(db_session, create_project_user(user_id=user1.id, project_id=project.id))
    project_user2 = await add_to_db(
        db_session,
        create_project_user(
            user_id=user2.id,
            project_id=project.id,
            role_id=envs.DEFAULT_ROLE_OPENSTACK_ID
        )
    )
    await db_session.commit()

    access_token = create_access_token(user_id=user1.id)

    # when
    response = await client.post(
        f"/projects/{project.id}/users/{user2.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # then
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "USER_ROLE_ALREADY_IN_PROJECT"
