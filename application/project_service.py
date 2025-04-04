from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from exception.project_exception import ProjectNotFoundException
from infrastructure.database import transactional
from infrastructure.project.repository import ProjectRepository


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository = Depends()
    ):
        self.project_repository = project_repository

    @transactional()
    async def find_projects(
        self,
        session: AsyncSession,
        ids: list[int] | None = None,
        name: str | None = None,
        name_like: str | None = None,
        sort_by: ProjectSortOption = ProjectSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_relations: bool = False,
    ) -> list[Project]:
        projects: list[Project] = await self.project_repository.find_all(
            session=session,
            ids=ids,
            name=name,
            name_like=name_like,
            sort_by=sort_by,
            order=order,
            with_relations=with_relations
        )
        return projects

    @transactional()
    async def get_project(
        self,
        session: AsyncSession,
        project_id: int,
        with_relations: bool = False,
    ) -> Project:
        project: Project | None = await self.project_repository.find_by_id(
            session=session,
            project_id=project_id,
            with_relations=with_relations
        )

        if not project:
            raise ProjectNotFoundException()

        return project
