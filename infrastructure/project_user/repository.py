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

    async def create_project_user(
        self,
        session: AsyncSession,
        project_user: ProjectUser,
    ) -> None:
        session.add(project_user)
        await session.flush()
