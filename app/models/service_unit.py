from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class ServiceUnit(TimestampMixin, Base):
    __tablename__ = "service_units"

    church_id: Mapped[int] = mapped_column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    leader_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    church: Mapped["Church"] = relationship("Church", back_populates="service_units")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="service_units")
    leader: Mapped["User | None"] = relationship("User", back_populates="led_units", foreign_keys=[leader_id])
