from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class KeystoneToken:
    token: str
    expires_at: datetime

    @classmethod
    def from_token(cls, token: str, expires_at: str) -> "KeystoneToken":
        return cls(
            token=token,
            expires_at=datetime.strptime(expires_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        )
