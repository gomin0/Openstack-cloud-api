from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.enum import SortOrder
from domain.user.entitiy import User
from domain.user.enum import UserSortOption
from exception.user_exception import UserNotFoundException
from infrastructure.database import transactional
from infrastructure.user.repository import UserRepository


class UserService:
    def __init__(
        self,
        user_repository: UserRepository = Depends()
    ):
        self.user_repository = user_repository

    @transactional()
    async def find_users(
        self,
        session: AsyncSession,
        user_id: int | None = None,
        account_id: str | None = None,
        name: str | None = None,
        sort_by: UserSortOption = UserSortOption.CREATED_AT,
        sort_order: SortOrder = SortOrder.ASC,
        with_relations: bool = False,
    ) -> list[User]:
        users: list[User] = await self.user_repository.find_all(
            session=session,
            user_id=user_id,
            account_id=account_id,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order,
            with_relations=with_relations,
        )
        return users

    @transactional()
    async def get_user(
        self,
        session: AsyncSession,
        user_id: int,
        with_relations: bool = False,
    ) -> User:
        user: User | None = await self.user_repository.find_by_id(
            session=session,
            user_id=user_id,
            with_relations=with_relations,
        )

        if not user:
            raise UserNotFoundException()

        return user
