from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class FollowUpTask(TimestampMixin, Base):
    __tablename__ = "follow_up_tasks"

    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    assigned_to: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(
        Enum("call", "message", "visit", "invite", "other", name="task_type"),
        nullable=False,
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "overdue", name="task_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="task_priority"),
        nullable=False,
        default="medium",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="tasks")
    assigned_user: Mapped["User | None"] = relationship("User", back_populates="tasks", foreign_keys=[assigned_to])
    reminders: Mapped[list["Reminder"]] = relationship("Reminder", back_populates="task")


class CommunicationLog(TimestampMixin, Base):
    __tablename__ = "communication_logs"

    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(
        Enum("whatsapp", "sms", "call", "email", "manual", "visit", name="communication_channel"),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("sent", "delivered", "failed", "read", name="communication_status"),
        nullable=False,
        default="sent",
    )
    sent_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="communication_logs")
    sender: Mapped["User | None"] = relationship("User", back_populates="communication_logs", foreign_keys=[sent_by])


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("follow_up_tasks.id"), nullable=False, index=True)
    reminder_type: Mapped[str] = mapped_column(
        Enum("due", "second", "escalation", name="reminder_type"),
        nullable=False,
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "sent", "failed", name="reminder_status"),
        nullable=False,
        default="pending",
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["FollowUpTask"] = relationship("FollowUpTask", back_populates="reminders")
