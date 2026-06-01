from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    church_id: int
    branch_id: int
    name: str = Field(min_length=1, max_length=200)
    trigger_event: str = Field(
        pattern="^(contact_created|task_completed|no_response|overdue|contact_reengaged)$"
    )
    target_category: str = Field(
        pattern="^(first_timer|new_convert|outreach_convert|member|all)$"
    )
    rules_json: dict[str, Any] | None = None
    active: bool = True


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    trigger_event: str | None = Field(
        default=None,
        pattern="^(contact_created|task_completed|no_response|overdue|contact_reengaged)$",
    )
    target_category: str | None = Field(
        default=None,
        pattern="^(first_timer|new_convert|outreach_convert|member|all)$",
    )
    rules_json: dict[str, Any] | None = None
    active: bool | None = None
    branch_id: int | None = None


class WorkflowResponse(BaseModel):
    id: int
    church_id: int
    branch_id: int
    name: str
    trigger_event: str
    target_category: str
    active: bool
    rules_json: dict[str, Any] | None
    branch_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowListResponse(BaseModel):
    items: list[WorkflowResponse]
    total: int
    page: int
    page_size: int


class WorkflowFilter(BaseModel):
    trigger_event: str | None = None
    target_category: str | None = None
    active: bool | None = None
    branch_id: int | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
