from sqlalchemy import select, Select, ScalarResult, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from domain.enum import SortOrder, LifecycleStatus
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
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> list[Project]:
        query: Select[tuple[Project]] = select(Project)

        if not with_deleted:
            query = query.where(Project.lifecycle_status == LifecycleStatus.ACTIVE)

        if with_relations:
            query = query.options(
                joinedload(Project._domain),
                selectinload(Project._linked_users).selectinload(ProjectUser._user)
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

        result: ScalarResult[Project] = await session.scalars(query)
        return list(result.all())

    async def find_by_id(
        self,
        session: AsyncSession,
        project_id: int,
        with_deleted: bool = False,
        with_relations: bool = False
    ) -> Project | None:
        query: Select[tuple[Project]] = select(Project).where(Project.id == project_id)

        if not with_deleted:
            query = query.where(Project.lifecycle_status == LifecycleStatus.ACTIVE)
        if with_relations:
            query = query.options(
                joinedload(Project._domain),
                selectinload(Project._linked_users).selectinload(ProjectUser._user)
            )

        result: Project | None = await session.scalar(query)
        return result

    async def exists_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> bool:
        result: bool = await session.scalar(
            select(
                exists().where(
                    Project.name == name,
                    Project.lifecycle_status == LifecycleStatus.ACTIVE,
                )
            )
        )
        return result

    async def update_with_optimistic_lock(
        self,
        session: AsyncSession,
        project: Project,
    ) -> Project:
        await session.flush()
        return project
