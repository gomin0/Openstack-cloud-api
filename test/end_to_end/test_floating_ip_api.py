from unittest.mock import Mock

from test.util.database import add_to_db
from test.util.factory import (
    create_domain, create_user, create_project,
    create_project_user, create_access_token,
)


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
