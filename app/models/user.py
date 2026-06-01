from sqlalchemy import Boolean, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="role")


class Permission(TimestampMixin, Base):
    __tablename__ = "permissions"

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    permission_key: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_key", name="uq_role_permission"),
    )

    role: Mapped["Role"] = relationship("Role", back_populates="permissions")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("roles.id"), nullable=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    church: Mapped["Church"] = relationship("Church", back_populates="users", foreign_keys=[church_id])
    branch: Mapped["Branch"] = relationship("Branch", back_populates="users", foreign_keys=[branch_id])
    role: Mapped["Role | None"] = relationship("Role", back_populates="users")
    assigned_contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="assigned_worker", foreign_keys="Contact.assigned_worker_id")
    tasks: Mapped[list["FollowUpTask"]] = relationship("FollowUpTask", back_populates="assigned_user", foreign_keys="FollowUpTask.assigned_to")
    led_units: Mapped[list["ServiceUnit"]] = relationship("ServiceUnit", back_populates="leader", foreign_keys="ServiceUnit.leader_id")
    templates_created: Mapped[list["MessageTemplate"]] = relationship("MessageTemplate", back_populates="creator", foreign_keys="MessageTemplate.created_by")
    communication_logs: Mapped[list["CommunicationLog"]] = relationship("CommunicationLog", back_populates="sender", foreign_keys="CommunicationLog.sent_by")
