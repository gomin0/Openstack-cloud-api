from unittest.mock import Mock

from test.util.database import add_to_db
from test.util.factory import create_domain, create_user, create_project, create_security_group, \
    create_server, create_server_security_group, create_access_token


async def test_find_security_groups_success(client, db_session, mock_async_client):
    # given
    domain = await add_to_db(db_session, create_domain())
    user = await add_to_db(db_session, create_user(domain_id=domain.id))
    project = await add_to_db(db_session, create_project(domain_id=domain.id))

    security_group1 = await add_to_db(db_session, create_security_group(project_id=project.id))
    security_group2 = await add_to_db(db_session, create_security_group(project_id=project.id))

    server = await add_to_db(db_session, create_server(project_id=project.id))
    await add_to_db(db_session, create_server_security_group(server_id=server.id, security_group_id=security_group1.id))

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
