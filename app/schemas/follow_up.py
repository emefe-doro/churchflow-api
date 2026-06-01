from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    contact_id: int
    assigned_to: int | None = None
    task_type: str = Field(pattern="^(call|message|visit|invite|other)$")
    due_date: datetime | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    notes: str | None = None


class TaskUpdate(BaseModel):
    task_type: str | None = Field(default=None, pattern="^(call|message|visit|invite|other)$")
    due_date: datetime | None = None
    status: str | None = Field(default=None, pattern="^(pending|in_progress|completed|overdue)$")
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    notes: str | None = None


class TaskAssign(BaseModel):
    assigned_to: int


class TaskNotes(BaseModel):
    notes: str = Field(min_length=1)


class TaskPriority(BaseModel):
    priority: str = Field(pattern="^(low|medium|high)$")


class TaskResponse(BaseModel):
    id: int
    contact_id: int
    assigned_to: int | None
    task_type: str
    due_date: datetime | None
    status: str
    priority: str
    notes: str | None
    completed_at: datetime | None
    contact_name: str | None = None
    assigned_user_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskFilter(BaseModel):
    contact_id: int | None = None
    assigned_to: int | None = None
    task_type: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
