from dataclasses import dataclass


@dataclass
class CreateServerCommand:
    @dataclass
    class RootVolume:
        size: int
        image_openstack_id: str

    keystone_token: str
    current_project_id: int
    current_project_openstack_id: str
    name: str
    description: str
    flavor_openstack_id: str
    network_openstack_id: str
    root_volume: RootVolume
    security_group_ids: list[int]
