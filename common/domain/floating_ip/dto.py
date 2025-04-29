from pydantic.dataclasses import dataclass

from common.domain.floating_ip.enum import FloatingIpStatus


@dataclass
class FloatingIpDTO:
    openstack_id: str
    status: FloatingIpStatus
    address: str
