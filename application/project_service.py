from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from exception.project_exception import ProjectNotFoundException
from infrastructure.database import transactional
from infrastructure.project_repository import ProjectRepository


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
    ) -> list[Project]:
        projects = await self.project_repository.find_all(session, ids, name, name_like, sort_by, order, joined=True)
        return projects

    @transactional()
    async def get_project(
        self,
        session: AsyncSession,
        project_id: int,
    ) -> Project:
        project = await self.project_repository.find_by_id(session, project_id, joined=True)

        if not project:
            raise ProjectNotFoundException()

        return project
