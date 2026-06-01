from typing import Any

from pydantic import BaseModel, field_validator


class WorkerSummaryItem(BaseModel):
    worker_id: int
    worker_name: str
    total_tasks: int
    pending: int
    completed: int
    overdue: int


class DashboardResponse(BaseModel):
    church_id: int
    pending_tasks: int
    overdue_tasks: int
    completed_tasks: int
    first_timers_this_week: int
    new_converts_this_week: int
    total_first_timers: int = 0
    return_rate: float = 0.0
    retention_rate: float = 0.0
    worker_summary: list[WorkerSummaryItem]

    @field_validator("return_rate", "retention_rate", mode="before")
    @classmethod
    def coerce_rate(cls, v: Any) -> float:
        if v is None:
            return 0.0
        try:
            result = float(v)
            if result != result:
                return 0.0
            return max(0.0, result)
        except (ValueError, TypeError):
            return 0.0
