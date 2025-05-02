from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.orm.attributes import Mapped
from sqlalchemy.sql.sqltypes import DateTime


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
    deleted_at: Mapped[datetime | None] = mapped_column("deleted_at", DateTime, nullable=True)

    def delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)


class BaseEntity(AsyncAttrs, DeclarativeBase, TimestampMixin):
    __abstract__ = True


class SoftDeleteBaseEntity(BaseEntity, SoftDeleteMixin):
    __abstract__ = True
