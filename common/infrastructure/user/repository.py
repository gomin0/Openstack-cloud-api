from typing import Sequence

from sqlalchemy import select, Select, ScalarResult, exists, ColumnElement
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.functions import count

from common.domain.enum import SortOrder
from common.domain.project.entity import ProjectUser
from common.domain.user.entity import User
from common.domain.user.enum import UserSortOption
from common.exception.common_exception import MultipleEntitiesFoundException
from common.infrastructure.database import session_factory


class UserRepository:
    async def find_all(
        self,
        user_id: int | None = None,
        account_id: str | None = None,
        name: None | str = None,
        sort_by: UserSortOption = UserSortOption.CREATED_AT,
        sort_order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> list[User]:
        async with session_factory() as session:
            query: Select[tuple[User]] = select(User)

            if not with_deleted:
                query = query.where(User.deleted_at.is_(None))
            if with_relations:
                query = query.options(
                    joinedload(User._domain),
                    selectinload(User._linked_projects).selectinload(ProjectUser._project)
                )
            if user_id:
                query = query.where(User.id == user_id)
            if account_id:
                query = query.where(User.account_id == account_id)
            if name:
                query = query.where(User.name == name)

            order_by_column = {
                UserSortOption.CREATED_AT: User.created_at,
                UserSortOption.ACCOUNT_ID: User.account_id,
                UserSortOption.NAME: User.name
            }.get(sort_by)

            if sort_order == SortOrder.DESC:
                order_by_column = order_by_column.desc()

            query = query.order_by(order_by_column)

            result: ScalarResult[User] = await session.scalars(query)
            return list(result.all())

    async def find_by_id(
        self,

        user_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> User | None:
        async with session_factory() as session:
            query: Select[tuple[User]] = select(User).where(User.id == user_id)

            if not with_deleted:
                query = query.where(User.deleted_at.is_(None))
            if with_relations:
                query = query.options(
                    joinedload(User._domain),
                    selectinload(User._linked_projects).selectinload(ProjectUser._project)
                )

            return await session.scalar(query)

    async def find_by_account_id(
        self,
        account_id: str,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> User | None:
        async with session_factory() as session:
            query: Select = select(User).where(User.account_id == account_id)

            if not with_deleted:
                query = query.where(User.deleted_at.is_(None))
            if with_relations:
                query = query.options(
                    joinedload(User._domain),
                    selectinload(User._linked_projects).selectinload(ProjectUser._project)
                )

            result: ScalarResult[User] = await session.scalars(query)
            users: Sequence[User] = result.all()
            if len(users) > 1:
                raise MultipleEntitiesFoundException()
            return users[0] if len(users) == 1 else None

    async def exists_by_account_id(self, account_id: str) -> bool:
        async with session_factory() as session:
            is_not_deleted: ColumnElement = User.deleted_at.is_(None)
            query: Select = select(exists().where(is_not_deleted, User.account_id == account_id))
            return await session.scalar(query)

    async def count_by_domain(self, domain_id: int, with_deleted: bool = False) -> int:
        async with session_factory() as session:
            query = select(count()).select_from(User).where(User.domain_id == domain_id)
            if not with_deleted:
                query = query.where(User.deleted_at.is_(None))
            return await session.scalar(query)

    async def create(self, user: User) -> User:
        async with session_factory() as session:
            session.add(user)
            await session.flush()
            return user
