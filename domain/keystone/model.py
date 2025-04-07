from dataclasses import dataclass
from datetime import datetime


@dataclass
class KeystoneToken:
    token: str
    expires_at: datetime
