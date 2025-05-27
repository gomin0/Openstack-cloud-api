from sqlalchemy import String, BigInteger, CHAR
from sqlalchemy.orm import Mapped, mapped_column

from common.domain.entity import SoftDeleteBaseEntity


class Domain(SoftDeleteBaseEntity):
    __tablename__ = "domain"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(32), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
