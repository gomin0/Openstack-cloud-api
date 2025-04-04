from sqlalchemy import select, Select, Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from domain.enum import SortOrder
from domain.project.entity import Project, ProjectUser
from domain.project.enum import ProjectSortOption


class ProjectRepository:
    async def find_all(
        self,
        session: AsyncSession,
        ids: list[int] | None = None,
        name: str | None = None,
        name_like: str | None = None,
        sort_by: ProjectSortOption = ProjectSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_relations: bool = False
    ) -> list[Project]:
        query: Select[tuple[Project]] = select(Project)

        if with_relations:
            query = query.options(
                joinedload(Project.domain),
                selectinload(Project.linked_users).selectinload(ProjectUser.user)
            )

        if ids:
            query = query.where(Project.id.in_(ids))
        if name:
            query = query.where(Project.name == name)
        if name_like:
            query = query.where(Project.name.like(f"%{name_like}%"))

        order_by_column = {
            ProjectSortOption.NAME: Project.name,
            ProjectSortOption.CREATED_AT: Project.created_at
        }.get(sort_by, Project.created_at)

        if order == SortOrder.DESC:
            order_by_column = order_by_column.desc()

        query = query.order_by(order_by_column)

        result: Result[tuple[Project]] = await session.execute(query)
        return list(result.scalars().all())

    async def find_by_id(
        self,
        session: AsyncSession,
        project_id: int,
        with_relations: bool = False
    ) -> Project | None:
        query: Select[tuple[Project]] = select(Project).where(Project.id == project_id)

        if with_relations:
            query = query.options(
                joinedload(Project.domain),
                selectinload(Project.linked_users).selectinload(ProjectUser.user)
            )

        result: Result[tuple[Project]] = await session.execute(query)
        return result.scalar_one_or_none()
