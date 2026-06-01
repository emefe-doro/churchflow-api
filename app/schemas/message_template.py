from datetime import datetime

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    church_id: int
    branch_id: int
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(pattern="^(first_timer|new_convert|outreach|service_unit|general)$")
    channel: str = Field(default="manual", pattern="^(whatsapp|sms|email|manual)$")
    body: str = Field(min_length=1)
    created_by: int | None = None


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, pattern="^(first_timer|new_convert|outreach|service_unit|general)$")
    channel: str | None = Field(default=None, pattern="^(whatsapp|sms|email|manual)$")
    body: str | None = Field(default=None, min_length=1)
    branch_id: int | None = None


class TemplateResponse(BaseModel):
    id: int
    church_id: int
    branch_id: int
    name: str
    category: str
    channel: str
    body: str
    approved: bool
    created_by: int | None
    creator_name: str | None = None
    branch_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int
    page: int
    page_size: int


class TemplateFilter(BaseModel):
    category: str | None = None
    channel: str | None = None
    approved: bool | None = None
    branch_id: int | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
