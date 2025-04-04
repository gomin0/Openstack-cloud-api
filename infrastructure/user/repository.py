from sqlalchemy import select, Select, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from domain.enum import SortOrder
from domain.project.entity import ProjectUser
from domain.user.entitiy import User
from domain.user.enum import UserSortOption


class UserRepository:
    async def find_all(
        self,
        session: AsyncSession,
        user_id: int | None = None,
        account_id: str | None = None,
        name: None | str = None,
        sort_by: UserSortOption = UserSortOption.CREATED_AT,
        sort_order: SortOrder = SortOrder.ASC,
        with_relations: bool = False,
    ) -> list[User]:
        query: Select[tuple[User]] = select(User)

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
        }.get(sort_by, User.created_at)

        if sort_order == SortOrder.DESC:
            order_by_column = order_by_column.desc()

        query = query.order_by(order_by_column)

        result: ScalarResult[User] = await session.scalars(query)
        return list(result.all())
