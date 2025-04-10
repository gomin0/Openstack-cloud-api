from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from domain.project.entity import ProjectUser


class ProjectUserRepository:
    async def exists_by_user_and_project(
        self,
        session: AsyncSession,
        project_id: int,
        user_id: int
    ) -> bool:
        stmt = select(exists().where(
            ProjectUser.project_id == project_id,
            ProjectUser.user_id == user_id
        ))
        result = await session.execute(stmt)
        return result.scalar()
