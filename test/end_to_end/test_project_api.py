from domain.domain.entity import Domain
from domain.project.entity import Project, ProjectUser
from domain.user.entitiy import User


async def find_projects_setup(async_db_session):
    domain = Domain(openstack_id="domain123", name="도메인1")
    user1 = User(openstack_id="user123", _domain=domain, account_id="user1", name="사용자1", password="@!#32")
    user2 = User(openstack_id="user456", _domain=domain, account_id="user2", name="사용자2", password="@!@3")
    project1 = Project(openstack_id="project123", _domain=domain, name="프로젝트1")
    project2 = Project(openstack_id="project456", _domain=domain, name="프로젝트2")

    async_db_session.add_all([domain, user1, user2, project1, project2])
    await async_db_session.flush()

    project_user1 = ProjectUser(user_id=user1.id, project_id=project1.id, role_id="role123")
    project_user2 = ProjectUser(user_id=user2.id, project_id=project1.id, role_id="role123")

    async_db_session.add_all([project_user1, project_user2])
    await async_db_session.flush()
    await async_db_session.commit()


async def test_find_projects(async_client, db_session):
    # given
    await find_projects_setup(db_session)

    # when
    response = await async_client.get("/projects")

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


async def test_find_projects_with_name_like(async_client, db_session):
    # given
    await find_projects_setup(db_session)

    # when
    response = await async_client.get("/projects?name_like=2")

    # then
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 1
    assert data["projects"][0]["name"] == "프로젝트2"


async def test_get_project(async_client, db_session):
    # given
    domain = Domain(openstack_id="domainabc", name="도메인2")
    user = User(openstack_id="ted123", _domain=domain, account_id="abc", name="ted", password="@!#32")
    project = Project(openstack_id="project12345", _domain=domain, name="프로젝트")

    db_session.add_all([domain, user, project])
    await db_session.flush()

    project_user = ProjectUser(_user=user, project_id=project.id, role_id="role123")

    db_session.add_all([project_user])
    await db_session.flush()
    await db_session.commit()

    # when
    response = await async_client.get(f"/projects/{project.id}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == "프로젝트"
    assert data["domain"]["id"] == domain.id
    assert data["domain"]["name"] == "도메인2"
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["name"] == "ted"


async def test_get_project_fail_not_found(async_client):
    # given
    project_id = 999999

    # when
    response = await async_client.get(f"/projects/{project_id}")

    # then
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PROJECT_NOT_FOUND"
