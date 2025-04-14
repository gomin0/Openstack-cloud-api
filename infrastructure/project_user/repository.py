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

        result = await session.scalar(stmt)
        return result

    async def is_user_role_exist(
        self,
        session: AsyncSession,
        project_id: int,
        user_id: int,
        role_id: str
    ) -> bool:
        result: bool = await session.scalar(
            select(
                exists().where(
                    ProjectUser.project_id == project_id,
                    ProjectUser.user_id == user_id,
                    ProjectUser.role_id == role_id
                )
            )
        )
        return result

    async def add_user_role(
        self,
        session: AsyncSession,
        project_user: ProjectUser,
    ) -> None:
        session.add(project_user)
        await session.flush()
