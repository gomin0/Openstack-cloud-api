from dataclasses import dataclass

from common.domain.volume.enum import VolumeStatus


@dataclass
class VolumeDto:
    openstack_id: int
    volume_type_name: str
    image_openstack_id: str | None
    status: VolumeStatus
    size: int
