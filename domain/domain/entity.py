from datetime import datetime

from sqlalchemy import String, DateTime, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column

from domain.enum import EntityStatus
from infrastructure.database import Base


class Domain(Base):
    __tablename__ = "domain"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    status: Mapped[EntityStatus] = mapped_column(
        "status", String(15), nullable=False, default=EntityStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)
