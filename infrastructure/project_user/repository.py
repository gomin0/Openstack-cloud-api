from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from domain.project.entity import ProjectUser


class ProjectUserRepository:
    async def exists_by_project_and_user(
        self,
        session: AsyncSession,
        project_id: int,
        user_id: int
    ) -> bool:
        stmt = select(exists().where(
            ProjectUser.project_id == project_id,
            ProjectUser.user_id == user_id
        ))
        result: bool = await session.scalar(stmt)
        return result

    async def find_by_project_and_user(
        self,
        session: AsyncSession,
        project_id: int,
        user_id: int,
    ) -> ProjectUser | None:
        project_user: ProjectUser | None = await session.scalar(
            select(ProjectUser).where(
                ProjectUser.project_id == project_id,
                ProjectUser.user_id == user_id,
            )
        )
        return project_user

    async def create_project_user(
        self,
        session: AsyncSession,
        project_user: ProjectUser,
    ) -> None:
        session.add(project_user)
        await session.flush()

    async def remove_user_role(
        self,
        session: AsyncSession,
        project_user: ProjectUser,
    ) -> None:
        await session.delete(project_user)
        await session.flush()
