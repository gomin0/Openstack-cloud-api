from datetime import datetime

from sqlalchemy import String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import Base


class ProjectUser(Base):
    __tablename__ = "project_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("role.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )