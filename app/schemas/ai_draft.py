from pydantic import BaseModel, Field


class AIDraftRequest(BaseModel):
    contact_id: int
    category: str = Field(
        pattern="^(first_timer|new_convert|outreach_convert|service_unit|general)$"
    )
    channel: str = Field(default="whatsapp", pattern="^(whatsapp|sms|email|manual)$")
    branch_id: int
    tone: str | None = Field(
        default=None, pattern="^(warm|caring|encouraging|formal|concise|pastoral)$"
    )
    additional_context: str | None = Field(default=None, max_length=1000)
    override_prompt: str | None = Field(default=None, max_length=2000)


class AIDraftResponse(BaseModel):
    id: int
    contact_id: int
    body: str
    status: str
    source: str
    source_label: str
    template_used: str | None = None
    template_id: int | None = None
    token_count: int | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    category: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class AIDraftGenerateResponse(BaseModel):
    success: bool
    draft: AIDraftResponse | None = None
    source: str
    message: str
    fallback_used: bool = False


class AIDraftBatchRequest(BaseModel):
    contact_ids: list[int] = Field(min_length=1, max_length=50)
    category: str = Field(
        pattern="^(first_timer|new_convert|outreach_convert|service_unit|general)$"
    )
    channel: str = Field(default="whatsapp", pattern="^(whatsapp|sms|email|manual)$")
    branch_id: int
    tone: str | None = Field(
        default=None, pattern="^(warm|caring|encouraging|formal|concise|pastoral)$"
    )
    additional_context: str | None = Field(default=None, max_length=1000)


class AIDraftBatchResponse(BaseModel):
    success: int
    failed: int
    skipped: int
    results: list[AIDraftGenerateResponse]
