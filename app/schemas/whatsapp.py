from datetime import datetime

from pydantic import BaseModel, Field


class WhatsAppMessageCreate(BaseModel):
    contact_id: int
    branch_id: int
    template_id: int | None = None
    body: str = Field(min_length=1)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    scheduled_at: datetime | None = None


class WhatsAppMessageUpdate(BaseModel):
    body: str | None = None
    priority: str | None = Field(default=None, pattern="^(low|normal|high)$")
    scheduled_at: datetime | None = None


class WhatsAppApprovalAction(BaseModel):
    approved: bool
    rejected_reason: str | None = Field(default=None, min_length=1)


class WhatsAppMessageResponse(BaseModel):
    id: int
    church_id: int
    branch_id: int
    contact_id: int
    template_id: int | None
    body: str
    status: str
    priority: str
    created_by: int | None
    approved_by: int | None
    approved_at: datetime | None
    rejected_reason: str | None
    external_message_id: str | None
    scheduled_at: datetime | None
    contact_name: str | None = None
    contact_phone: str | None = None
    template_name: str | None = None
    creator_name: str | None = None
    approver_name: str | None = None
    branch_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WhatsAppMessageListResponse(BaseModel):
    items: list[WhatsAppMessageResponse]
    total: int
    page: int
    page_size: int


class WhatsAppMessageFilter(BaseModel):
    contact_id: int | None = None
    status: str | None = None
    priority: str | None = None
    template_id: int | None = None
    created_by: int | None = None
    scheduled_from: datetime | None = None
    scheduled_to: datetime | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class WhatsAppQueueItemResponse(BaseModel):
    id: int
    message_id: int
    status: str
    attempt_count: int
    max_attempts: int
    next_attempt_at: datetime | None
    last_error: str | None
    external_message_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WhatsAppQueueStatusResponse(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    total: int


class WhatsAppDeliveryLogResponse(BaseModel):
    id: int
    message_id: int
    external_message_id: str | None
    status: str
    event_timestamp: datetime | None
    raw_payload: dict | None
    error_code: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WhatsAppDeliveryLogListResponse(BaseModel):
    items: list[WhatsAppDeliveryLogResponse]
    total: int


class WhatsAppOptOutCreate(BaseModel):
    phone_number: str = Field(min_length=5, max_length=20)
    contact_id: int | None = None
    reason: str | None = None
    source: str = Field(default="manual", pattern="^(manual|webhook|incoming_message)$")


class WhatsAppOptOutResponse(BaseModel):
    id: int
    church_id: int
    contact_id: int | None
    phone_number: str
    reason: str | None
    source: str
    opted_out_at: datetime | None
    contact_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WhatsAppOptOutListResponse(BaseModel):
    items: list[WhatsAppOptOutResponse]
    total: int
    page: int
    page_size: int


class WhatsAppOptOutFilter(BaseModel):
    phone_number: str | None = None
    contact_id: int | None = None
    source: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class WhatsAppWebhookPayload(BaseModel):
    object: str | None = None
    entry: list[dict] | None = None
