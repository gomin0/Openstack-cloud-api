from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.orm.attributes import Mapped
from sqlalchemy.sql.sqltypes import DateTime, Enum

from common.domain.enum import LifecycleStatus


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )


class SoftDeleteMixin:
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        Enum(LifecycleStatus, name="lifecycle_status", native_enum=False, length=15),
        nullable=False,
        default=LifecycleStatus.ACTIVE
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)

    def mark_as_deleted(self) -> None:
        self.lifecycle_status = LifecycleStatus.MARK_DELETED
        self.deleted_at = datetime.now(timezone.utc)

    def delete(self) -> None:
        self.lifecycle_status = LifecycleStatus.DELETED
        self.deleted_at = datetime.now(timezone.utc)


class BaseEntity(AsyncAttrs, DeclarativeBase, TimestampMixin):
    __abstract__ = True


class SoftDeleteBaseEntity(BaseEntity, SoftDeleteMixin):
    __abstract__ = True
