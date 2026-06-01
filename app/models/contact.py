from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        Enum("first_timer", "new_convert", "outreach_convert", "member", "other", name="contact_category"),
        nullable=False,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(
        Enum("service", "outreach", "online", "referral", "other", name="contact_source"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("new", "contacted", "follow_up", "attending", "inactive", "completed", name="contact_status"),
        nullable=False,
        default="new",
        index=True,
    )
    assigned_worker_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    foundation_class_status: Mapped[str | None] = mapped_column(
        Enum("not_started", "invited", "attending", "completed", name="foundation_class_status"),
        nullable=True,
    )
    foundation_class_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    foundation_class_completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    baptism_status: Mapped[str | None] = mapped_column(
        Enum("not_baptized", "preparing", "baptized", name="baptism_status"),
        nullable=True,
    )
    cell_group: Mapped[str | None] = mapped_column(String(200), nullable=True)
    assigned_mentor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    service_unit_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("service_units.id"), nullable=True, index=True
    )
    service_unit_joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unit_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    second_visit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    third_visit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attendance_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    church: Mapped["Church"] = relationship("Church", foreign_keys=[church_id])
    branch: Mapped["Branch"] = relationship("Branch", foreign_keys=[branch_id])
    assigned_worker: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_worker_id])
    assigned_mentor: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_mentor_id])
    service_unit: Mapped["ServiceUnit | None"] = relationship("ServiceUnit", foreign_keys=[service_unit_id])
    tasks: Mapped[list["FollowUpTask"]] = relationship("FollowUpTask", back_populates="contact")
    communication_logs: Mapped[list["CommunicationLog"]] = relationship("CommunicationLog", back_populates="contact")
