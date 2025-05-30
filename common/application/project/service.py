import backoff
from fastapi import Depends
from sqlalchemy.orm.exc import StaleDataError

from common.application.project.response import ProjectDetailsResponse, ProjectDetailResponse, ProjectResponse
from common.domain.enum import SortOrder
from common.domain.project.entity import Project, ProjectUser
from common.domain.project.enum import ProjectSortOption
from common.domain.user.entity import User
from common.exception.project_exception import ProjectNotFoundException, UserAlreadyInProjectException, \
    ProjectAccessDeniedException, ProjectNameDuplicatedException, UserNotInProjectException
from common.exception.user_exception import UserNotFoundException
from common.infrastructure.database import transactional
from common.infrastructure.keystone.client import KeystoneClient
from common.infrastructure.project.repository import ProjectRepository
from common.infrastructure.project_user.repository import ProjectUserRepository
from common.infrastructure.user.repository import UserRepository
from common.util.compensating_transaction import CompensationManager
from common.util.envs import Envs, get_envs
from common.util.system_token_manager import get_system_keystone_token

envs: Envs = get_envs()


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

    @transactional
    async def find_projects_details(
        self,
        ids: list[int] | None = None,
        name: str | None = None,
        name_like: str | None = None,
        sort_by: ProjectSortOption = ProjectSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> ProjectDetailsResponse:
        projects: list[Project] = await self.project_repository.find_all(
            ids=ids,
            name=name,
            name_like=name_like,
            sort_by=sort_by,
            order=order,
            with_deleted=with_deleted,
            with_relations=with_relations
        )

        return ProjectDetailsResponse(
            projects=[await ProjectDetailResponse.from_entity(project) for project in projects]
        )

    @transactional
    async def get_project_detail(
        self,
        project_id: int,
        with_deleted: bool = False,
        with_relations: bool = False,
    ) -> ProjectDetailResponse:
        project: Project | None = await self.project_repository.find_by_id(
            project_id=project_id,
            with_deleted=with_deleted,
            with_relations=with_relations
        )

        if not project:
            raise ProjectNotFoundException()

        return await ProjectDetailResponse.from_entity(project)

    @backoff.on_exception(backoff.expo, StaleDataError, max_tries=3)
    @transactional
    async def update_project(
        self,
        compensating_tx: CompensationManager,
        user_id: int,
        project_id: int,
        new_name: str,
    ) -> ProjectResponse:
        project: Project | None = await self.project_repository.find_by_id(project_id=project_id)

        if not project:
            raise ProjectNotFoundException()

        old_name: str = project.name

        if not await self.project_user_repository.exists_by_project_and_user(project_id=project_id, user_id=user_id):
            raise ProjectAccessDeniedException()

        if await self.project_repository.exists_by_name(name=new_name):
            raise ProjectNameDuplicatedException()

        project.update_name(new_name)
        project: Project = await self.project_repository.update_with_optimistic_lock(project=project)

        project_openstack_id: str = project.openstack_id
        await self.keystone_client.update_project(
            project_openstack_id=project_openstack_id,
            name=new_name,
            keystone_token=get_system_keystone_token()
        )
        compensating_tx.add_task(
            lambda: self.keystone_client.update_project(
                project_openstack_id=project_openstack_id,
                name=old_name,
                keystone_token=get_system_keystone_token()
            )
        )

        return ProjectResponse.from_entity(project)

    @transactional
    async def assign_user_on_project(
        self,
        compensating_tx: CompensationManager,
        request_user_id: int,
        project_id: int,
        user_id: int
    ) -> None:
        project: Project | None = await self.project_repository.find_by_id(project_id=project_id)
        if not project:
            raise ProjectNotFoundException()

        if not await self.project_user_repository.exists_by_project_and_user(
            project_id=project_id, user_id=request_user_id
        ):
            raise ProjectAccessDeniedException()

        user: User | None = await self.user_repository.find_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundException()

        if await self.project_user_repository.exists_by_project_and_user(project_id=project_id, user_id=user_id):
            raise UserAlreadyInProjectException()

        await self.project_user_repository.create(
            project_user=ProjectUser(project_id=project_id, user_id=user_id)
        )

        project_openstack_id: str = project.openstack_id
        user_openstack_id: str = user.openstack_id
        await self.keystone_client.assign_role_to_user_on_project(
            project_openstack_id=project_openstack_id,
            user_openstack_id=user_openstack_id,
            role_openstack_id=envs.DEFAULT_ROLE_OPENSTACK_ID,
            keystone_token=get_system_keystone_token()
        )
        compensating_tx.add_task(
            lambda: self.keystone_client.unassign_role_from_user_on_project(
                project_openstack_id=project_openstack_id,
                user_openstack_id=user_openstack_id,
                role_openstack_id=envs.DEFAULT_ROLE_OPENSTACK_ID,
                keystone_token=get_system_keystone_token()
            )
        )

    @transactional
    async def unassign_user_from_project(
        self,
        compensating_tx: CompensationManager,
        request_user_id: int,
        project_id: int,
        user_id: int
    ) -> None:
        project: Project | None = await self.project_repository.find_by_id(project_id=project_id)
        if not project:
            raise ProjectNotFoundException()

        if not await self.project_user_repository.exists_by_project_and_user(
            project_id=project_id, user_id=request_user_id
        ):
            raise ProjectAccessDeniedException()

        user: User | None = await self.user_repository.find_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundException()

        project_user: ProjectUser | None = await self.project_user_repository.find_by_project_and_user(
            project_id=project_id, user_id=user_id
        )
        if not project_user:
            raise UserNotInProjectException()

        await self.project_user_repository.delete(project_user=project_user)

        project_openstack_id: str = project.openstack_id
        user_openstack_id: str = user.openstack_id
        await self.keystone_client.unassign_role_from_user_on_project(
            project_openstack_id=project_openstack_id,
            user_openstack_id=user_openstack_id,
            role_openstack_id=envs.DEFAULT_ROLE_OPENSTACK_ID,
            keystone_token=get_system_keystone_token()
        )
        compensating_tx.add_task(
            lambda: self.keystone_client.assign_role_to_user_on_project(
                project_openstack_id=project_openstack_id,
                user_openstack_id=user_openstack_id,
                role_openstack_id=envs.DEFAULT_ROLE_OPENSTACK_ID,
                keystone_token=get_system_keystone_token()
            )
        )
