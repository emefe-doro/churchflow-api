from datetime import datetime

from pydantic import BaseModel, Field


COMMUNICATION_CHANNELS = ["whatsapp", "sms", "call", "email", "manual", "visit"]


class CommunicationLogCreate(BaseModel):
    contact_id: int
    channel: str = Field(pattern="^(whatsapp|sms|call|email|manual|visit)$")
    sent_by: int | None = None
    sent_at: datetime | None = None
    message: str | None = None
    outcome: str | None = None
    provider: str | None = None


class CommunicationLogUpdate(BaseModel):
    channel: str | None = Field(default=None, pattern="^(whatsapp|sms|call|email|manual|visit)$")
    sent_by: int | None = None
    sent_at: datetime | None = None
    message: str | None = None
    outcome: str | None = None
    provider: str | None = None


class CommunicationLogResponse(BaseModel):
    id: int
    contact_id: int
    channel: str
    message: str | None
    provider: str | None
    outcome: str | None
    status: str
    sent_by: int | None
    sent_at: datetime | None
    contact_name: str | None = None
    contact_phone: str | None = None
    worker_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommunicationLogListResponse(BaseModel):
    items: list[CommunicationLogResponse]
    total: int
    page: int
    page_size: int


class CommunicationLogFilter(BaseModel):
    contact_id: int | None = None
    channel: str | None = None
    sent_by: int | None = None
    outcome: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
