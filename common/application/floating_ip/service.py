from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.application.floating_ip.response import FloatingIpDetailsResponse, FloatingIpDetailResponse
from common.domain.enum import SortOrder
from common.domain.floating_ip.entity import FloatingIp
from common.domain.floating_ip.enum import FloatingIpSortOption
from common.exception.floating_ip_exception import FloatingIpNotFoundException, FloatingIpAccessDeniedException
from common.infrastructure.database import transactional
from infrastructure.floating_ip.repository import FloatingIpRepository


class FloatingIpService:
    def __init__(
        self,
        floating_ip_repository: FloatingIpRepository = Depends()
    ):
        self.floating_ip_repository = floating_ip_repository

    @transactional()
    async def find_floating_ips_details(
        self,
        session: AsyncSession,
        project_id: int,
        sort_by: FloatingIpSortOption = FloatingIpSortOption.CREATED_AT,
        order: SortOrder = SortOrder.ASC,
        with_deleted: bool = False,
    ) -> FloatingIpDetailsResponse:
        floating_ips: list[FloatingIp] = await self.floating_ip_repository.find_all_by_project_id(
            session=session,
            project_id=project_id,
            sort_by=sort_by,
            order=order,
            with_deleted=with_deleted,
            with_relations=True
        )

        return FloatingIpDetailsResponse(
            floating_ips=[await FloatingIpDetailResponse.from_entity(floating_ip) for floating_ip in floating_ips]
        )

    @transactional()
    async def get_floating_ip_detail(
        self,
        session: AsyncSession,
        project_id: int,
        floating_ip_id: int,
        with_deleted: bool = False,
    ) -> FloatingIpDetailResponse:
        floating_ip: FloatingIp | None = await self.floating_ip_repository.find_by_id(
            session=session,
            floating_ip_id=floating_ip_id,
            with_deleted=with_deleted,
            with_relations=True
        )
        if not floating_ip:
            raise FloatingIpNotFoundException()

        if project_id != floating_ip.project_id:
            raise FloatingIpAccessDeniedException()

        return await FloatingIpDetailResponse.from_entity(floating_ip)
