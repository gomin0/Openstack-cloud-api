import asyncio

import bcrypt
from fastapi import Depends

from common.application.user.response import UserDetailResponse, UserResponse
from common.domain.enum import SortOrder
from common.domain.user.entity import User
from common.domain.user.enum import UserSortOption
from common.exception.user_exception import (
    UserNotFoundException, UserAccountIdDuplicateException, UserUpdatePermissionDeniedException,
    LastUserDeletionNotAllowedException
)
from common.infrastructure.database import transactional
from common.infrastructure.keystone.client import KeystoneClient
from common.infrastructure.user.repository import UserRepository
from common.util.compensating_transaction import CompensationManager
from common.util.envs import get_envs, Envs
from common.util.system_token_manager import get_system_keystone_token

envs: Envs = get_envs()


class UserService:
    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        keystone_client: KeystoneClient = Depends(),
    ):
        self.user_repository = user_repository
        self.keystone_client = keystone_client

    @transactional
    async def find_user_details(
        self,
        user_id: int | None = None,
        account_id: str | None = None,
        name: str | None = None,
        sort_by: UserSortOption = UserSortOption.CREATED_AT,
        sort_order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> list[UserDetailResponse]:
        users: list[User] = await self.user_repository.find_all(
            user_id=user_id,
            account_id=account_id,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order,
            with_deleted=with_deleted,
            with_relations=with_relations,
        )
        return [await UserDetailResponse.from_entity(user) for user in users]

    @transactional
    async def get_user_detail(
        self,
        user_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> UserDetailResponse:
        user: User | None = await self.user_repository.find_by_id(
            user_id=user_id,
            with_deleted=with_deleted,
            with_relations=with_relations,
        )

        if not user:
            raise UserNotFoundException()

        return await UserDetailResponse.from_entity(user)

    @transactional
    async def create_user(
        self,
        compensating_tx: CompensationManager,
        account_id: str,
        name: str,
        password: str,
    ) -> UserResponse:
        # Check duplication
        is_account_id_exists: bool = await self.user_repository.exists_by_account_id(account_id=account_id)
        if is_account_id_exists:
            raise UserAccountIdDuplicateException(account_id=account_id)

        # Create user in OpenStack
        user_openstack_id: str = await self.keystone_client.create_user(
            domain_openstack_id=envs.DEFAULT_DOMAIN_OPENSTACK_ID,
            keystone_token=get_system_keystone_token(),
            password=password,
        )
        compensating_tx.add_task(
            lambda: self.keystone_client.delete_user(
                keystone_token=get_system_keystone_token(),
                user_openstack_id=user_openstack_id,
            )
        )

        # Create user in DB
        hashed_password: bytes = await asyncio.to_thread(
            bcrypt.hashpw,
            password.encode("UTF-8"),
            bcrypt.gensalt()
        )
        user: User = await self.user_repository.create(
            user=User.create(
                openstack_id=user_openstack_id,
                domain_id=envs.DEFAULT_DOMAIN_ID,
                account_id=account_id,
                name=name,
                hashed_password=hashed_password.decode("UTF-8"),
            )
        )
        return UserResponse.from_entity(user)

    @transactional
    async def update_user_info(
        self,
        request_user_id: int,
        user_id: int,
        name: str,
    ) -> UserResponse:
        if request_user_id != user_id:
            raise UserUpdatePermissionDeniedException()

        user: User | None = await self.user_repository.find_by_id(user_id=user_id)
        if user is None:
            raise UserNotFoundException()

        user.update_info(name=name)
        return UserResponse.from_entity(user)

    @transactional
    async def delete_user(
        self,
        current_user_id: int,
        user_id: int,
    ) -> None:
        user: User | None = await self.user_repository.find_by_id(user_id=user_id)
        if user is None:
            raise UserNotFoundException()
        user.validate_delete_permission(req_user_id=current_user_id)

        num_of_users: int = await self.user_repository.count_by_domain(domain_id=user.domain_id)
        if num_of_users <= 1:
            raise LastUserDeletionNotAllowedException()

        await self.keystone_client.delete_user(
            keystone_token=get_system_keystone_token(),
            user_openstack_id=user.openstack_id,
        )

        await user.delete()
