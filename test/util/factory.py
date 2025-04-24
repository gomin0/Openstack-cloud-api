from datetime import datetime, timezone, timedelta
from typing import Any

import bcrypt
from async_property import async_property

from common import auth_token_manager
from common.envs import Envs, get_envs
from domain.domain.entity import Domain
from domain.enum import LifecycleStatus
from domain.keystone.model import KeystoneToken
from domain.project.entity import Project, ProjectUser
from domain.security_group.entity import SecurityGroup
from domain.server.entity import Server
from domain.server.enum import ServerStatus
from domain.user.entity import User
from test.util.random import random_string, random_int

envs: Envs = get_envs()


def create_domain(
    domain_id: int | None = envs.DEFAULT_DOMAIN_ID,
    openstack_id: str = envs.DEFAULT_DOMAIN_OPENSTACK_ID,
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
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE,
    deleted_at: datetime | None = None,
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


def create_security_group(
    security_group_id: int | None = None,
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    name: str = random_string(),
    description: str = random_string(),
) -> SecurityGroup:
    return SecurityGroup(
        id=security_group_id,
        openstack_id=openstack_id,
        project_id=project_id,
        name=name,
        description=description,
    )


def create_server(
    server_id: int | None = None,
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    flavor_openstack_id: str = random_string(),
    name: str = random_string(),
    description: str = random_string(),
    status: ServerStatus = ServerStatus.ACTIVE,
) -> Server:
    return Server(
        id=server_id,
        openstack_id=openstack_id,
        project_id=project_id,
        flavor_openstack_id=flavor_openstack_id,
        name=name,
        description=description,
        status=status,
    )


def create_security_group_stub(
    security_group_id: int,
    name: str = random_string(),
    description: str = random_string(),
    project_id: int = random_int(),
    openstack_id: str = random_string(),
    created_at: datetime = datetime.now(timezone.utc),
    updated_at: datetime = datetime.now(timezone.utc),
    deleted_at: datetime | None = None,
    servers: list[Server] | None = None
) -> SecurityGroup:
    return SecurityGroupStub(
        id=security_group_id,
        name=name,
        description=description,
        project_id=project_id,
        openstack_id=openstack_id,
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
        servers=servers or []
    )


def create_access_token(
    user_id: int = random_int(),
    user_openstack_id: str = random_string(),
    project_id: int = random_int(),
    project_openstack_id: str = random_string(),
    keystone_token: str = random_string(),
    keystone_token_expires_at: datetime = datetime.now(timezone.utc) + timedelta(minutes=60),
) -> str:
    return auth_token_manager.create_access_token(
        user_id=user_id,
        user_openstack_id=user_openstack_id,
        project_id=project_id,
        project_openstack_id=project_openstack_id,
        keystone_token=KeystoneToken(
            token=keystone_token,
            expires_at=keystone_token_expires_at
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


class SecurityGroupStub(SecurityGroup):
    def __init__(self, servers: list[Server] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._mock_servers = servers

    @async_property
    async def servers(self):
        return self._mock_servers
