from datetime import datetime, timezone, timedelta

import bcrypt

from common import auth_token_manager
from domain.domain.entity import Domain
from domain.keystone.model import KeystoneToken
from domain.project.entity import Project, ProjectUser
from domain.user.entity import User
from test.util.random import random_string, random_int


def create_domain(
    domain_id: int | None = None,
    openstack_id: str = random_string(),
    name: str = random_string(),
) -> Domain:
    return Domain(
        id=domain_id,
        openstack_id=openstack_id,
        name=name,
    )


def create_project(
    domain_id: int,
    project_id: int | None = None,
    openstack_id: str = random_string(),
    name: str = random_string(),
    version: int = 0
) -> Project:
    return Project(
        id=project_id,
        domain_id=domain_id,
        openstack_id=openstack_id,
        name=name,
        version=version
    )


def create_user(
    user_id: int | None = None,
    domain_id: int = random_int(),
    openstack_id: str = random_string(),
    account_id: str = random_string(),
    name: str = random_string(),
    plain_password: str = random_string(),
) -> User:
    return User(
        id=user_id,
        domain_id=domain_id,
        openstack_id=openstack_id,
        account_id=account_id,
        name=name,
        password=bcrypt.hashpw(
            password=plain_password.encode("UTF-8"),
            salt=bcrypt.gensalt()
        ).decode("UTF-8"),
    )


def create_project_user(
    user_id: int,
    project_id: int,
    project_user_id: int | None = None,
) -> ProjectUser:
    return ProjectUser(
        id=project_user_id,
        user_id=user_id,
        project_id=project_id,
    )


def create_access_token(
    user_id: int,
    project_id: int = random_int(),
    token: str = random_string(),
    expires_at: datetime = datetime.now(timezone.utc) + timedelta(minutes=60)
) -> str:
    return auth_token_manager.create_access_token(
        user_id=user_id,
        project_id=project_id,
        keystone_token=KeystoneToken(
            token=token,
            expires_at=expires_at
        )
    )
