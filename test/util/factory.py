from datetime import datetime, timezone, timedelta
from typing import Any

import bcrypt
from async_property import async_property

from common.domain.domain.entity import Domain
from common.domain.floating_ip.entity import FloatingIp
from common.domain.floating_ip.enum import FloatingIpStatus
from common.domain.keystone.model import KeystoneToken
from common.domain.network_interface.entity import NetworkInterface
from common.domain.project.entity import Project, ProjectUser
from common.domain.security_group.entity import SecurityGroup
from common.domain.server.entity import Server
from common.domain.server.enum import ServerStatus
from common.domain.user.entity import User
from common.domain.volume.entity import Volume
from common.domain.volume.enum import VolumeStatus
from common.util import auth_token_manager
from common.util.envs import Envs, get_envs
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
    server_id: int = random_int(),
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    flavor_openstack_id: str = random_string(),
    name: str = random_string(),
    description: str = random_string(),
    status: ServerStatus = ServerStatus.ACTIVE,
    created_at: datetime = datetime.now(timezone.utc),
    updated_at: datetime = datetime.now(timezone.utc),
    deleted_at: datetime | None = None,
) -> Server:
    return Server(
        id=server_id,
        openstack_id=openstack_id,
        project_id=project_id,
        flavor_openstack_id=flavor_openstack_id,
        name=name,
        description=description,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
    )


def create_server_stub(
    volumes: list[Volume],
    network_interfaces: list[NetworkInterface],
    security_groups: list[SecurityGroup],
    server_id: int | None = None,
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    flavor_openstack_id: str = random_string(),
    name: str = random_string(),
    description: str = random_string(),
    status: ServerStatus = ServerStatus.ACTIVE,
    created_at: datetime = datetime.now(timezone.utc),
    updated_at: datetime = datetime.now(timezone.utc),
    deleted_at: datetime | None = None,
) -> Server:
    return ServerStub(
        id=server_id,
        openstack_id=openstack_id,
        project_id=project_id,
        flavor_openstack_id=flavor_openstack_id,
        name=name,
        description=description,
        status=status,
        volumes=volumes,
        network_interfaces=network_interfaces,
        security_groups=security_groups,
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
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


def create_floating_ip(
    floating_ip_id: int | None = None,
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    network_interface_id: int | None = None,
    status: FloatingIpStatus = FloatingIpStatus.DOWN,
    address: str = random_string()
) -> FloatingIp:
    return FloatingIp(
        id=floating_ip_id,
        openstack_id=openstack_id,
        project_id=project_id,
        network_interface_id=network_interface_id,
        status=status,
        address=address,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
    )


def create_floating_ip_stub(
    project_id: int,
    network_interface: NetworkInterface | None = None,
    floating_ip_id: int = random_int(),
    openstack_id: str = random_string(),
    status: FloatingIpStatus = FloatingIpStatus.DOWN,
    address: str = random_string(),
    created_at: datetime = datetime.now(timezone.utc),
    updated_at: datetime = datetime.now(timezone.utc),
    deleted_at: datetime | None = None,
) -> FloatingIp:
    return FloatingIpStub(
        id=floating_ip_id,
        openstack_id=openstack_id,
        project_id=project_id,
        network_interface_id=network_interface.id if network_interface else None,
        status=status,
        address=address,
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
        network_interface=network_interface
    )


def create_volume(
    volume_id: int = random_int(),
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    server_id: int | None = None,
    volume_type_openstack_id: str = random_string(),
    image_openstack_id: str | None = None,
    name: str = random_string(),
    description: str = random_string(),
    status: VolumeStatus = VolumeStatus.AVAILABLE,
    size: int = random_int(),
    is_root_volume: bool = False,
    deleted_at: datetime | None = None,
) -> Volume:
    return Volume(
        id=volume_id,
        openstack_id=openstack_id,
        project_id=project_id,
        server_id=server_id,
        volume_type_openstack_id=volume_type_openstack_id,
        image_openstack_id=image_openstack_id,
        name=name,
        description=description,
        status=status,
        size=size,
        is_root_volume=is_root_volume,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=deleted_at,
    )


def create_volume_stub(
    volume_id: int = random_int(),
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    server_id: int | None = None,
    volume_type_openstack_id: str = random_string(),
    image_openstack_id: str | None = None,
    name: str = random_string(),
    description: str = random_string(),
    status: VolumeStatus = VolumeStatus.AVAILABLE,
    size: int = random_int(),
    is_root_volume: bool = False,
    deleted_at: datetime | None = None,
    project: Project | None = None,
    server: Server | None = None,
) -> Volume:
    return VolumeStub(
        project=project or create_project(domain_id=random_int(), project_id=project_id),
        server=server,
        id=volume_id,
        openstack_id=openstack_id,
        project_id=project_id,
        server_id=server_id,
        volume_type_openstack_id=volume_type_openstack_id,
        image_openstack_id=image_openstack_id,
        name=name,
        description=description,
        status=status,
        size=size,
        is_root_volume=is_root_volume,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=deleted_at,
    )


def create_network_interface(
    server_id: int,
    project_id: int,
    network_interface_id: int = random_int(),
    openstack_id: str = random_string(),
    fixed_ip_address: str = random_string(),
) -> NetworkInterface:
    return NetworkInterface(
        id=network_interface_id,
        openstack_id=openstack_id,
        server_id=server_id,
        project_id=project_id,
        fixed_ip_address=fixed_ip_address,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
    )


def create_network_interface_stub(
    network_interface_id: int = random_int(),
    openstack_id: str = random_string(),
    project_id: int = random_int(),
    server_id: int | None = None,
    fixed_ip_address: str = random_string(),
    server: Server | None = None,
    floating_ip: FloatingIp | None = None,
    deleted_at: datetime | None = None,
) -> NetworkInterface:
    return NetworkInterfaceStub(
        server=server,
        floating_ip=floating_ip,
        id=network_interface_id,
        openstack_id=openstack_id,
        project_id=project_id,
        server_id=server_id,
        fixed_ip_address=fixed_ip_address,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=deleted_at,
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


class FloatingIpStub(FloatingIp):
    def __init__(self, network_interface: NetworkInterface | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._mock_network_interface: NetworkInterface | None = network_interface

    @async_property
    async def network_interface(self) -> NetworkInterface | None:
        return self._mock_network_interface


class SecurityGroupStub(SecurityGroup):
    def __init__(self, servers: list[Server] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._mock_servers = servers

    @async_property
    async def servers(self) -> list[Server]:
        return self._mock_servers


class VolumeStub(Volume):
    def __init__(self, project: Project, server: Server | None = None, **kwargs):
        super().__init__(**kwargs)
        self._mock_project = project
        self._mock_server = server

    @async_property
    async def project(self) -> Project:
        return self._mock_project

    @async_property
    async def server(self) -> Server | None:
        return self._mock_server


class ServerStub(Server):
    def __init__(
        self,
        volumes: list[Volume],
        network_interfaces: list[NetworkInterface],
        security_groups: list[SecurityGroup],
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self._mock_volumes: list[Volume] = volumes
        self._mock_network_interfaces: list[NetworkInterface] = network_interfaces
        self._mock_security_groups: list[SecurityGroup] = security_groups

    @async_property
    async def volumes(self) -> list[Volume]:
        return self._mock_volumes

    @async_property
    async def network_interfaces(self) -> list[NetworkInterface]:
        return self._mock_network_interfaces

    @async_property
    async def security_groups(self) -> list[SecurityGroup]:
        return self._mock_security_groups


class NetworkInterfaceStub(NetworkInterface):
    def __init__(
        self,
        server: Server | None,
        floating_ip: FloatingIp | None,
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.mock_server = server
        self._mock_floating_ip: FloatingIp = floating_ip

    @async_property
    async def floating_ip(self) -> FloatingIp | None:
        return self._mock_floating_ip

    @async_property
    async def server(self) -> Server | None:
        return self.mock_server
