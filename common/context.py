from dataclasses import dataclass


@dataclass
class CurrentUser:
    user_id: int
    keystone_token: str
