import backoff
from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from common.compensating_transaction import CompensationManager
from domain.enum import SortOrder
from domain.project.entity import Project
from domain.project.enum import ProjectSortOption
from exception.openstack_exception import OpenStackException
from exception.project_exception import ProjectNotFoundException, ProjectNameDuplicatedException, \
    ProjectAccessDeniedException
from infrastructure.database import transactional
from infrastructure.keystone.client import KeystoneClient
from infrastructure.project.repository import ProjectRepository
from infrastructure.project_user.repository import ProjectUserRepository
from infrastructure.user.repository import UserRepository


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository = Depends(),
        user_repository: UserRepository = Depends(),
        project_user_repository: ProjectUserRepository = Depends(),
        keystone_client: KeystoneClient = Depends()
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.project_user_repository = project_user_repository
        self.keystone_client = keystone_client

    @transactional()
    async def find_projects(
        self,
        session: AsyncSession,
        ids: list[int] | None = None,
        name: str | None = None,
        name_like: str | None = None,
        sort_by: ProjectSortOption = ProjectSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> list[Project]:
        projects: list[Project] = await self.project_repository.find_all(
            session=session,
            ids=ids,
            name=name,
            name_like=name_like,
            sort_by=sort_by,
            order=order,
            with_deleted=with_deleted,
            with_relations=with_relations
        )
        return projects

    @transactional()
    async def get_project(
        self,
        session: AsyncSession,
        project_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> Project:
        project: Project | None = await self.project_repository.find_by_id(
            session=session,
            project_id=project_id,
            with_deleted=with_deleted,
            with_relations=with_relations
        )

        if not project:
            raise ProjectNotFoundException()

        return project

    @backoff.on_exception(backoff.expo, StaleDataError, max_tries=5)
    @transactional()
    async def update_project(
        self,
        compensating_tx: CompensationManager,
        session: AsyncSession,
        client: AsyncClient,
        keystone_token: str,
        user_id: int,
        project_id: int,
        new_name: str,
    ) -> Project | None:
        project: Project | None = await self.project_repository.find_by_id(
            session=session,
            project_id=project_id,
        )

        if not project:
            raise ProjectNotFoundException()

        old_name: str = project.name

        if not await self.project_user_repository.exists_user(
            session=session,
            project_id=project_id,
            user_id=user_id,
        ):
            raise ProjectAccessDeniedException()

        if await self.project_repository.exists_by_name(
            session=session,
            name=new_name,
        ):
            raise ProjectNameDuplicatedException()

        project.update_name(new_name)
        project: Project = await self.project_repository.update_with_optimistic_lock(session, project)

        try:
            project_openstack_id: str = project.openstack_id
            await self.keystone_client.update_project(
                client=client,
                project_openstack_id=project_openstack_id,
                name=new_name,
                keystone_token=keystone_token
            )
            compensating_tx.add_task(
                lambda: self.keystone_client.update_project(
                    client=client,
                    project_openstack_id=project_openstack_id,
                    name=old_name,
                    keystone_token=keystone_token
                )
            )
        except OpenStackException as ex:
            if ex.openstack_status_code == 403:
                raise ProjectAccessDeniedException() from ex
            if ex.openstack_status_code == 409:
                raise ProjectNameDuplicatedException() from ex
            raise ex

        return project
