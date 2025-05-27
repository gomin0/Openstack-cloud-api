from sqlalchemy import select, exists

from common.domain.project.entity import ProjectUser
from common.infrastructure.database import session_factory


class ProjectUserRepository:
    async def exists_by_project_and_user(
        self,
        project_id: int,
        user_id: int
    ) -> bool:
        async with session_factory() as session:
            stmt = select(exists().where(
                ProjectUser.project_id == project_id,
                ProjectUser.user_id == user_id
            ))

            result: bool = await session.scalar(stmt)
            return result

    async def find_by_project_and_user(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectUser | None:
        async with session_factory() as session:
            project_user: ProjectUser | None = await session.scalar(
                select(ProjectUser).where(
                    ProjectUser.project_id == project_id,
                    ProjectUser.user_id == user_id,
                )
            )
            return project_user

    async def create(
        self,
        project_user: ProjectUser,
    ) -> None:
        async with session_factory() as session:
            session.add(project_user)
            await session.flush()

    async def delete(
        self,
        project_user: ProjectUser,
    ) -> None:
        async with session_factory() as session:
            await session.delete(project_user)
            await session.flush()
