from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class MessageTemplate(TimestampMixin, Base):
    __tablename__ = "message_templates"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum("first_timer", "new_convert", "outreach", "service_unit", "general", name="template_category"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        Enum("whatsapp", "sms", "email", "manual", name="template_channel"),
        nullable=False,
        default="manual",
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    church: Mapped["Church"] = relationship("Church", back_populates="message_templates")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="message_templates")
    creator: Mapped["User | None"] = relationship("User", back_populates="templates_created", foreign_keys=[created_by])
