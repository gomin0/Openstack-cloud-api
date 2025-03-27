from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.domain import Domain
from domain.status import Status
from infrastructure.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column("uuid", CHAR(32), unique=True, nullable=False)
    domain_id: Mapped[str] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    account_id: Mapped[str] = mapped_column("account_id", String(20), nullable=False)
    name: Mapped[str] = mapped_column("name", String(15), nullable=False)
    password: Mapped[str] = mapped_column("password", String(255), nullable=False)
    status: Mapped[Status] = mapped_column(
        "status", Enum(Status), nullable=False, default=Status.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    domain: Mapped["Domain"] = relationship("Domain", lazy="select")
