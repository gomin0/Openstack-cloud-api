from datetime import datetime

from pydantic import BaseModel

from domain.security_group.enum import SecurityGroupRuleDirection


class SecurityGroupRuleDTO(BaseModel):
    id: str
    protocol: str | None = None
    direction: SecurityGroupRuleDirection
    port_range_min: int | None = None
    port_range_max: int | None = None
    remote_ip_prefix: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityGroupRuleDTO":
        return cls(
            id=data["id"],
            protocol=data.get("protocol"),
            direction=data["direction"],
            port_range_min=data.get("port_range_min"),
            port_range_max=data.get("port_range_max"),
            remote_ip_prefix=data.get("remote_ip_prefix"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
        )
