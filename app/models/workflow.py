from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Workflow(TimestampMixin, Base):
    __tablename__ = "workflows"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    trigger_event: Mapped[str] = mapped_column(
        Enum(
            "contact_created",
            "task_completed",
            "no_response",
            "overdue",
            "contact_reengaged",
            name="workflow_trigger",
        ),
        nullable=False,
    )
    target_category: Mapped[str] = mapped_column(
        Enum("first_timer", "new_convert", "outreach_convert", "member", "all", name="workflow_target"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rules_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    church: Mapped["Church"] = relationship("Church", back_populates="workflows")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="workflows")
