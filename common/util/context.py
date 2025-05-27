from dataclasses import dataclass


@dataclass
class CurrentUser:
    user_id: int
    user_openstack_id: str
    project_id: int
    project_openstack_id: str
    keystone_token: str
