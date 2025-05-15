from pydantic.dataclasses import dataclass


@dataclass
class OsNetworkInterfaceDto:
    openstack_id: str
    name: str
    network_openstack_id: str
    project_openstack_id: str
    status: str
    fixed_ip_address: str
