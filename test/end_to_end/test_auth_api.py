from datetime import datetime, timezone, timedelta

import httpx

from domain.domain.entity import Domain
from domain.project.entity import Project
from domain.user.entitiy import User
from test.end_to_end.conftest import mock_async_client
from test.util.database import add_to_db
from test.util.factory import create_user, create_domain, create_project, create_project_user
from test.util.random import random_string


async def test_login_success_without_project_id(client, db_session, mock_async_client):
    # given
    user_password: str = random_string()
    subject_token: str = random_string()
    expected_keystone_token_exp: datetime = datetime.now(timezone.utc) + timedelta(days=1)

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user: User = await add_to_db(db_session, create_user(domain_id=domain.id, plain_password=user_password))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()

    mock_async_client.request.return_value = httpx.Response(
        status_code=201,
        headers={
            "x-subject-token": subject_token,
        },
        json={
            "token": {
                "expires_at": expected_keystone_token_exp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
        }
    )

    # when
    response = await client.post(
        url="/auth/login",
        headers={"Content-Type": "application/json"},
        json={
            "account_id": user.account_id,
            "password": user_password,
        }
    )

    # then
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["user"]["id"] == user.id
    assert response_body.get("token") is not None


async def test_login_success_with_project_id(client, db_session, mock_async_client):
    # given
    plain_password: str = random_string()
    subject_token: str = random_string()
    expected_keystone_token_exp: datetime = datetime.now(timezone.utc) + timedelta(days=1)

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user: User = await add_to_db(db_session, create_user(domain_id=domain.id, plain_password=plain_password))
    await add_to_db(db_session, create_project_user(user_id=user.id, project_id=project.id))
    await db_session.commit()

    mock_async_client.request.return_value = httpx.Response(
        status_code=201,
        headers={
            "x-subject-token": subject_token,
        },
        json={
            "token": {
                "expires_at": expected_keystone_token_exp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
        }
    )

    # when
    response = await client.post(
        url="/auth/login",
        headers={"Content-Type": "application/json"},
        json={
            "account_id": user.account_id,
            "password": plain_password,
            "project_id": project.id,
        }
    )

    # then
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["user"]["id"] == user.id
    assert response_body.get("token") is not None


async def test_login_fail_user_authentication_failed(client, db_session, mock_async_client):
    # given
    plain_password: str = random_string()

    domain: Domain = await add_to_db(db_session, create_domain())
    user: User = await add_to_db(db_session, create_user(domain_id=domain.id, plain_password=plain_password))
    await db_session.commit()

    # when
    response = await client.post(
        url="/auth/login",
        headers={"Content-Type": "application/json"},
        json={
            "account_id": user.account_id,
            "password": "wrong_password",
        }
    )

    # then
    assert response.status_code == 401
    assert response.json().get("code") == "INVALID_AUTH"


async def test_login_fail_user_did_not_join_any_project(client, db_session, mock_async_client):
    # given
    plain_password: str = random_string()

    domain: Domain = await add_to_db(db_session, create_domain())
    user: User = await add_to_db(db_session, create_user(domain_id=domain.id, plain_password=plain_password))
    await db_session.commit()

    # when
    response = await client.post(
        url="/auth/login",
        headers={"Content-Type": "application/json"},
        json={
            "account_id": user.account_id,
            "password": plain_password,
        }
    )

    # then
    assert response.status_code == 400
    assert response.json().get("code") == "USER_NOT_JOINED_ANY_PROJECT"


async def test_login_fail_user_has_not_project_access_permission(client, db_session, mock_async_client):
    # given
    plain_password: str = random_string()

    domain: Domain = await add_to_db(db_session, create_domain())
    project: Project = await add_to_db(db_session, create_project(domain_id=domain.id))
    user: User = await add_to_db(db_session, create_user(domain_id=domain.id, plain_password=plain_password))
    await db_session.commit()

    # when
    response = await client.post(
        url="/auth/login",
        headers={"Content-Type": "application/json"},
        json={
            "account_id": user.account_id,
            "password": plain_password,
            "project_id": project.id,
        }
    )

    # then
    assert response.status_code == 403
    assert response.json().get("code") == "PROJECT_ACCESS_DENIED"
