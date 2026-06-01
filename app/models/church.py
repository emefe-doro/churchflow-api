from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Church(TimestampMixin, Base):
    __tablename__ = "churches"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    branches: Mapped[list["Branch"]] = relationship("Branch", back_populates="church")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="church", foreign_keys="Contact.church_id")
    users: Mapped[list["User"]] = relationship("User", back_populates="church", foreign_keys="User.church_id")
    service_units: Mapped[list["ServiceUnit"]] = relationship("ServiceUnit", back_populates="church")
    message_templates: Mapped[list["MessageTemplate"]] = relationship("MessageTemplate", back_populates="church")
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="church")


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pastor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    church: Mapped["Church"] = relationship("Church", back_populates="branches")
    pastor: Mapped["User | None"] = relationship("User", foreign_keys=[pastor_id])
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="branch", foreign_keys="Contact.branch_id")
    users: Mapped[list["User"]] = relationship("User", back_populates="branch", foreign_keys="User.branch_id")
    service_units: Mapped[list["ServiceUnit"]] = relationship("ServiceUnit", back_populates="branch")
    message_templates: Mapped[list["MessageTemplate"]] = relationship("MessageTemplate", back_populates="branch")
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="branch")
