from datetime import datetime, timezone, timedelta

import bcrypt

from common.auth_token_manager import create_access_token
from domain.domain.entity import Domain
from domain.keystone.model import KeystoneToken
from domain.project.entity import Project, ProjectUser
from domain.user.entitiy import User
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
        role_id=random_string(),
    )


def create_current_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    keystone_token = KeystoneToken(
        token="fake-keystone-token",
        expires_at=now + timedelta(minutes=60)
    )
    access_token = create_access_token(user_id=user.id, keystone_token=keystone_token)
    return access_token
