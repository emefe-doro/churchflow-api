from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class WhatsAppMessage(TimestampMixin, Base):
    __tablename__ = "whatsapp_messages"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    template_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("message_templates.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "pending_approval",
            "approved",
            "rejected",
            "queued",
            "sent",
            "delivered",
            "read",
            "failed",
            name="whatsapp_message_status",
        ),
        nullable=False,
        default="draft",
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        Enum("low", "normal", "high", name="whatsapp_message_priority"),
        nullable=False,
        default="normal",
    )
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    church: Mapped["Church"] = relationship("Church", foreign_keys=[church_id])
    branch: Mapped["Branch"] = relationship("Branch", foreign_keys=[branch_id])
    contact: Mapped["Contact"] = relationship("Contact", foreign_keys=[contact_id])
    template: Mapped["MessageTemplate | None"] = relationship("MessageTemplate", foreign_keys=[template_id])
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])
    queue_items: Mapped[list["WhatsAppQueueItem"]] = relationship("WhatsAppQueueItem", back_populates="message")
    delivery_logs: Mapped[list["WhatsAppDeliveryLog"]] = relationship("WhatsAppDeliveryLog", back_populates="message")


class WhatsAppQueueItem(TimestampMixin, Base):
    __tablename__ = "whatsapp_queue_items"

    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("whatsapp_messages.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "processing", "completed", "failed", name="queue_item_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    message: Mapped["WhatsAppMessage"] = relationship("WhatsAppMessage", back_populates="queue_items")


class WhatsAppDeliveryLog(TimestampMixin, Base):
    __tablename__ = "whatsapp_delivery_logs"

    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("whatsapp_messages.id"), nullable=False, index=True)
    external_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        Enum("sent", "delivered", "read", "failed", "deleted", name="delivery_log_status"),
        nullable=False,
    )
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    message: Mapped["WhatsAppMessage"] = relationship("WhatsAppMessage", back_populates="delivery_logs")


class WhatsAppOptOut(TimestampMixin, Base):
    __tablename__ = "whatsapp_opt_outs"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        Enum("manual", "webhook", "incoming_message", name="opt_out_source"),
        nullable=False,
        default="manual",
    )
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    church: Mapped["Church"] = relationship("Church", foreign_keys=[church_id])
    contact: Mapped["Contact | None"] = relationship("Contact", foreign_keys=[contact_id])
