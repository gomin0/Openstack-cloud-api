import asyncio

import bcrypt
from fastapi import Depends

from common.application.auth.response import LoginResponse, UserResponse
from common.domain.keystone.model import KeystoneToken
from common.domain.project.entity import Project
from common.domain.user.entity import User
from common.exception.auth_exception import InvalidAuthException
from common.exception.project_exception import ProjectAccessDeniedException
from common.exception.user_exception import UserNotJoinedAnyProjectException
from common.infrastructure.database import transactional
from common.infrastructure.keystone.client import KeystoneClient
from common.infrastructure.user.repository import UserRepository
from common.util.auth_token_manager import create_access_token
from common.util.envs import Envs, get_envs

envs: Envs = get_envs()


class AuthService:
    encoding: str = "UTF-8"

    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        keystone_client: KeystoneClient = Depends(),
    ):
        self.user_repository = user_repository
        self.keystone_client = keystone_client

    async def login(
        self,
        project_id: int | None,
        account_id: str,
        password: str,
    ) -> LoginResponse:
        # account_id, password로 유저 인증 및 조회
        user: User = await self._authenticate_user(account_id=account_id, password=password)

        # Keystone token 발급을 위한 프로젝트 선택
        project: Project = await self._choose_project(user=user, project_id=project_id)

        # Keystone token 발급
        keystone_token: KeystoneToken = await self._issue_keystone_token(
            user_openstack_id=user.openstack_id,
            password=password,
            project_openstack_id=project.openstack_id,
        )

        # Access token 발급
        access_token: str = create_access_token(
            user_id=user.id,
            user_openstack_id=user.openstack_id,
            project_id=project.id,
            project_openstack_id=project.openstack_id,
            keystone_token=keystone_token
        )

        return LoginResponse(user=UserResponse.from_entity(user), token=access_token)

    @transactional
    async def _authenticate_user(
        self,
        account_id: str,
        password: str,
    ) -> User:
        user: User | None = await self.user_repository.find_by_account_id(account_id=account_id, with_relations=True)
        if user is None:
            raise InvalidAuthException()

        is_valid_password: bool = await asyncio.to_thread(
            bcrypt.checkpw,
            password=password.encode(self.encoding),
            hashed_password=user.password.encode(self.encoding)
        )
        if not is_valid_password:
            raise InvalidAuthException()

        return user

    @transactional
    async def _choose_project(
        self,
        user: User,
        project_id: int | None
    ) -> Project:
        joined_projects: list[Project] = await user.projects
        if project_id is not None:
            # 선택된 프로젝트가 있다면, 선택된 프로젝트 조회
            project = next((proj for proj in joined_projects if proj.id == project_id), None)
            if project is None:
                raise ProjectAccessDeniedException(project_id=project_id)
            return project

        # 선택된 프로젝트가 없다면, 소속된 프로젝트 중 하나를 임의로 선택
        if len(joined_projects) == 0:
            raise UserNotJoinedAnyProjectException()
        return joined_projects[0]

    async def _issue_keystone_token(
        self,
        user_openstack_id: str,
        password: str,
        project_openstack_id: str,
    ) -> KeystoneToken:
        token: str
        expires_at: str
        token, expires_at = await self.keystone_client.authenticate_with_scoped_auth(
            user_openstack_id=user_openstack_id,
            domain_openstack_id=envs.DEFAULT_DOMAIN_OPENSTACK_ID,
            password=password,
            project_openstack_id=project_openstack_id,
        )
        return KeystoneToken.from_token(token=token, expires_at=expires_at)
