from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.domain.entity import Domain
from domain.enum import EntityStatus
from infrastructure.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    domain_id: Mapped[str] = mapped_column("domain_id", BigInteger, ForeignKey("domain.id"), nullable=False)
    account_id: Mapped[str] = mapped_column("account_id", String(20), nullable=False)
    name: Mapped[str] = mapped_column("name", String(15), nullable=False)
    password: Mapped[str] = mapped_column("password", String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        "status", String(15), nullable=False, default=EntityStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)

    domain: Mapped[Domain] = relationship("Domain", lazy="select")
