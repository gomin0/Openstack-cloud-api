from datetime import datetime

from pydantic.dataclasses import dataclass

from common.domain.enum import LifecycleStatus
from common.domain.floating_ip.enum import FloatingIpStatus


@dataclass
class FloatingIpDTO:
    id: int
    openstack_id: str
    project_id: int
    server_id: int | None
    status: FloatingIpStatus
    address: str
    lifecycle_status: LifecycleStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


@dataclass
class CreateFloatingIpDTO:
    openstack_id: str
    status: FloatingIpStatus
    address: str
