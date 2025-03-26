from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import Base


class Role(Base):
    __tablename__ = "role"

    id: Mapped[str] = mapped_column("id", String(255), nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True, default=None)
