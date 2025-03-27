from datetime import datetime

from sqlalchemy import String, DateTime, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column

from domain.entity_status import EntityStatus
from infrastructure.database import Base


class Domain(Base):
    __tablename__ = "domain"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column("uuid", CHAR(32), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        "status", String(15), nullable=False, default=EntityStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
