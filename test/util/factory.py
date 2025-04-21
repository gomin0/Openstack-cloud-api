from datetime import datetime, timezone, timedelta
from typing import Any

import bcrypt
from async_property import async_property

from common import auth_token_manager
from domain.domain.entity import Domain
from domain.enum import LifecycleStatus
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
        lifecycle_status=LifecycleStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
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


def create_project_stub(
    domain: Domain,
    users: list[User] = None,
    project_id: int | None = None,
    openstack_id: str = random_string(),
    name: str = random_string(),
    version: int = 0,
    created_at: datetime = datetime.now(timezone.utc),
    updated_at: datetime = datetime.now(timezone.utc),
    deleted_at: datetime | None = None
) -> Project:
    return ProjectStub(
        id=project_id,
        domain_id=domain.id,
        openstack_id=openstack_id,
        name=name,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
        users=users or [],
        domain=domain
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
        lifecycle_status=LifecycleStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
    )


def create_user_stub(
    user_id: int | None = None,
    domain_id: int = random_int(),
    openstack_id: str = random_string(),
    account_id: str = random_string(),
    name: str = random_string(),
    plain_password: str = random_string(),
    projects: list[Project] | None = None,
) -> User:
    return UserStub(
        domain=create_domain(domain_id=domain_id),
        projects=projects or [],
        id=user_id,
        domain_id=domain_id,
        openstack_id=openstack_id,
        account_id=account_id,
        name=name,
        password=bcrypt.hashpw(
            password=plain_password.encode("UTF-8"),
            salt=bcrypt.gensalt()
        ).decode("UTF-8"),
        lifecycle_status=LifecycleStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
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


class ProjectStub(Project):
    def __init__(self, domain: Domain, users: list[User] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._mock_users = users
        self._mock_domain = domain

    @async_property
    async def users(self):
        return self._mock_users

    @async_property
    async def domain(self):
        return self._mock_domain


class UserStub(User):
    def __init__(
        self,
        domain: Domain,
        projects: list[Project] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._mock_domain: Domain = domain
        self._mock_projects: list[Project] = projects or []

    @async_property
    async def domain(self) -> Domain:
        return self._mock_domain

    @async_property
    async def projects(self) -> list[Project]:
        return self._mock_projects
