from domain.domain.entity import Domain
from domain.project.entity import Project, ProjectUser
from domain.user.entitiy import User


async def test_get_project(async_client, async_db_session):
    # given
    domain = Domain(openstack_id="domainabc", name="도메인2")
    user = User(openstack_id="ted123", domain=domain, account_id="abc", name="ted", password="@!#32")
    project = Project(openstack_id="project12345", domain=domain, name="프로젝트")

    async_db_session.add_all([domain, user, project])
    await async_db_session.flush()

    project_user = ProjectUser(user=user, project_id=project.id, role_id="role123")

    async_db_session.add_all([project_user])
    await async_db_session.flush()
    await async_db_session.commit()

    # when
    response = await async_client.get(f"/projects/{project.id}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == "프로젝트"
    assert data["domain"]["id"] == domain.id
    assert data["domain"]["name"] == "도메인2"
    assert len(data["users"]) == 1
    assert data["users"][0]["name"] == "ted"
