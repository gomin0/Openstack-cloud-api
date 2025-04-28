from common.envs import get_envs
from test.util.database import add_to_db
from test.util.factory import (
    create_domain,
    create_user,
    create_project,
    create_project_user,
    create_floating_ip,
    create_access_token
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
