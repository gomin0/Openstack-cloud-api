from pydantic.dataclasses import dataclass

from common.domain.server.enum import ServerStatus


@dataclass
class OsServerDto:
    openstack_id: str
    project_openstack_id: str
    status: ServerStatus
    volume_openstack_ids: list[str]
