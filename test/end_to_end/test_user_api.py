from domain.domain.entity import Domain
from domain.project.entity import Project, ProjectUser
from domain.user.entitiy import User


async def find_users_setup(async_db_session):
    domain = Domain(openstack_id="domain123", name="도메인1")
    user1 = User(openstack_id="user123", _domain=domain, account_id="user1", name="사용자1", password="@!#32")
    user2 = User(openstack_id="user1234", _domain=domain, account_id="user2", name="사용자1", password="@!#32")
    project1 = Project(openstack_id="project123", _domain=domain, name="프로젝트1")
    project2 = Project(openstack_id="project456", _domain=domain, name="프로젝트2")

    async_db_session.add_all([domain, user1, user2, project1, project2])
    await async_db_session.flush()

    project_user1 = ProjectUser(user_id=user1.id, project_id=project1.id, role_id="role123")
    project_user2 = ProjectUser(user_id=user1.id, project_id=project2.id, role_id="role123")

    async_db_session.add_all([project_user1, project_user2])
    await async_db_session.flush()
    await async_db_session.commit()


async def test_find_users(async_client, db_session):
    # given
    await find_users_setup(db_session)

    # when
    response = await async_client.get("/users")

    # then
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) == 2

    user_data = None
    for u in data["users"]:
        if u["name"] == "사용자1":
            user_data = u
            break
    assert len(user_data["projects"]) == 2


async def test_find_users_with_account_id(async_client, db_session):
    # given
    await find_users_setup(db_session)
    user_id = "user1"

    # when
    response = await async_client.get(f"/users?account_id={user_id}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["users"][0]["account_id"] == user_id
