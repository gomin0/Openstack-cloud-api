from datetime import datetime
from unittest.mock import Mock

from sqlalchemy import select

from common.envs import Envs, get_envs
from domain.domain.entity import Domain
from domain.project.entity import Project, ProjectUser
from domain.user.entitiy import User
from router.user.request import CreateUserRequest
from test.util.database import add_to_db
from test.util.factory import create_domain, create_user
from test.util.random import random_string

envs: Envs = get_envs()


async def find_users_setup(db_session):
    domain = Domain(openstack_id="domain123", name="도메인1")
    db_session.add_all([domain])
    await db_session.flush()

    user1 = User(openstack_id="user123", domain_id=domain.id, account_id="user1", name="사용자1", password="@!#32")
    user2 = User(openstack_id="user1234", domain_id=domain.id, account_id="user2", name="사용자1", password="@!#32")
    project1 = Project(openstack_id="project123", domain_id=domain.id, name="프로젝트1")
    project2 = Project(openstack_id="project456", domain_id=domain.id, name="프로젝트2")

    db_session.add_all([domain, user1, user2, project1, project2])
    await db_session.flush()

    project_user1 = ProjectUser(user_id=user1.id, project_id=project1.id, role_id="role123")
    project_user2 = ProjectUser(user_id=user1.id, project_id=project2.id, role_id="role123")

    db_session.add_all([project_user1, project_user2])
    await db_session.flush()
    await db_session.commit()


async def test_find_users(client, db_session):
    # given
    await find_users_setup(db_session)

    # when
    response = await client.get("/users")

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


async def test_find_users_with_account_id(client, db_session):
    # given
    await find_users_setup(db_session)
    account_id = "user1"

    # when
    response = await client.get(f"/users?account_id={account_id}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["users"][0]["account_id"] == account_id


async def test_get_user(client, db_session):
    # given
    domain = Domain(openstack_id="domainabc", name="도메인2")

    db_session.add_all([domain])
    await db_session.flush()

    user = User(openstack_id="ted123", domain_id=domain.id, account_id="abc", name="ted", password="@!#32")
    project1 = Project(openstack_id="project12345", domain_id=domain.id, name="프로젝트1")
    project2 = Project(openstack_id="project123456", domain_id=domain.id, name="프로젝트2")

    db_session.add_all([user, project1, project2])
    await db_session.flush()

    project_user1 = ProjectUser(user_id=user.id, project_id=project1.id, role_id="role123")
    project_user2 = ProjectUser(user_id=user.id, project_id=project2.id, role_id="role123")

    db_session.add_all([project_user1, project_user2])
    await db_session.flush()
    await db_session.commit()

    # when
    response = await client.get(f"/users/{user.id}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["name"] == user.name
    assert data["domain"]["id"] == domain.id
    assert len(data["projects"]) == 2


async def test_get_project_fail_not_found(client):
    # given
    user_id = 9999

    # when
    response = await client.get(f"/users/{user_id}")

    # then
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "USER_NOT_FOUND"


async def test_create_user_success(client, db_session, mock_async_client):
    # given
    await add_to_db(db_session, create_domain(domain_id=envs.DEFAULT_DOMAIN_ID))
    await db_session.commit()

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "POST" and "/v3/auth/tokens" in url:
            mock_response.headers = {"x-subject-token": "keystone-token"}
            mock_response.json.return_value = {"token": {'expires_at': datetime.now()}}
        elif method == "POST" and "/v3/users" in url:
            mock_response.json.return_value = {"user": {"id": "user_openstack_id"}}
        else:
            raise ValueError("Unknown API endpoint")
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    request: CreateUserRequest = CreateUserRequest(
        account_id=random_string(),
        password=random_string(),
        name=random_string(),
    )

    # when
    response = await client.post(
        url="/users",
        headers={"Content-Type": "application/json"},
        json=request.model_dump(),
    )

    # then
    response_body = response.json()
    assert response.status_code == 201
    assert response_body["account_id"] == request.account_id
    assert response_body["name"] == request.name

    result = await db_session.scalars(select(User))
    users = result.all()
    assert len(users) == 1


async def test_create_user_fail_duplicate_account_id(client, db_session, mock_async_client):
    # given
    domain: Domain = await add_to_db(db_session, create_domain(domain_id=envs.DEFAULT_DOMAIN_ID))
    original_user: User = await add_to_db(db_session, create_user(domain_id=domain.id))
    await db_session.commit()

    def request_side_effect(method, url, *args, **kwargs):
        mock_response = Mock()
        if method == "POST" and "/v3/auth/tokens" in url:
            mock_response.headers = {"x-subject-token": "keystone-token"}
            mock_response.json.return_value = {"token": {'expires_at': datetime.now()}}
        elif method == "POST" and "/v3/users" in url:
            mock_response.json.return_value = {"user": {"id": "user_openstack_id"}}
        else:
            raise ValueError("Unknown API endpoint")
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        return mock_response

    mock_async_client.request.side_effect = request_side_effect

    request: CreateUserRequest = CreateUserRequest(
        account_id=original_user.account_id,
        password=random_string(),
        name=random_string(),
    )

    # when
    response = await client.post(
        url="/users",
        headers={"Content-Type": "application/json"},
        json=request.model_dump(),
    )

    # then
    assert mock_async_client.request.call_count == 0
    response_body = response.json()
    assert response.status_code == 409
    assert response_body["code"] == "USER_ACCOUNT_ID_DUPLICATE"
