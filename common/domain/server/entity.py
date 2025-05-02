from sqlalchemy import CHAR, BigInteger, ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.domain.entity import SoftDeleteBaseEntity
from common.domain.server.enum import ServerStatus


class Server(SoftDeleteBaseEntity):
    __tablename__ = "server"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    openstack_id: Mapped[str] = mapped_column("openstack_id", CHAR(36), nullable=False)
    project_id: Mapped[int] = mapped_column("project_id", BigInteger, ForeignKey("project.id"), nullable=False)
    flavor_openstack_id: Mapped[str] = mapped_column("flavor_openstack_id", CHAR(36), nullable=False)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    description: Mapped[str] = mapped_column("description", String(255), nullable=False)
    status: Mapped[ServerStatus] = mapped_column(
        Enum(ServerStatus, name="status", native_enum=False, length=30),
        nullable=False
    )

    _linked_security_groups: Mapped[list["ServerSecurityGroup"]] = relationship(
        "ServerSecurityGroup",
        lazy="select",
        back_populates="_server"
    )
