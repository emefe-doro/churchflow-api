from datetime import datetime

from pydantic import BaseModel, Field


class ContactCreate(BaseModel):
    church_id: int
    branch_id: int
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=20)
    age_group: str | None = Field(default=None, max_length=50)
    address: str | None = None
    category: str = Field(pattern="^(first_timer|new_convert|outreach_convert|member|other)$")
    source: str | None = Field(default=None, pattern="^(service|outreach|online|referral|other)$")
    status: str | None = Field(default="new", pattern="^(new|contacted|follow_up|attending|inactive|completed)$")
    assigned_worker_id: int | None = None
    foundation_class_status: str | None = Field(default=None, pattern="^(not_started|invited|attending|completed)$")
    foundation_class_start_date: datetime | None = None
    foundation_class_completion_date: datetime | None = None
    baptism_status: str | None = Field(default=None, pattern="^(not_baptized|preparing|baptized)$")
    cell_group: str | None = Field(default=None, max_length=200)
    assigned_mentor_id: int | None = None
    service_unit_id: int | None = None
    service_unit_joined_at: datetime | None = None
    unit_active: bool | None = None
    second_visit_date: datetime | None = None
    third_visit_date: datetime | None = None
    last_attendance_date: datetime | None = None
    notes: str | None = None
    consent_given: bool = False


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=20)
    age_group: str | None = Field(default=None, max_length=50)
    address: str | None = None
    category: str | None = Field(default=None, pattern="^(first_timer|new_convert|outreach_convert|member|other)$")
    source: str | None = Field(default=None, pattern="^(service|outreach|online|referral|other)$")
    status: str | None = Field(default=None, pattern="^(new|contacted|follow_up|attending|inactive|completed)$")
    assigned_worker_id: int | None = None
    foundation_class_status: str | None = Field(default=None, pattern="^(not_started|invited|attending|completed)$")
    foundation_class_start_date: datetime | None = None
    foundation_class_completion_date: datetime | None = None
    baptism_status: str | None = Field(default=None, pattern="^(not_baptized|preparing|baptized)$")
    cell_group: str | None = Field(default=None, max_length=200)
    assigned_mentor_id: int | None = None
    service_unit_id: int | None = None
    service_unit_joined_at: datetime | None = None
    unit_active: bool | None = None
    second_visit_date: datetime | None = None
    third_visit_date: datetime | None = None
    last_attendance_date: datetime | None = None
    notes: str | None = None
    consent_given: bool | None = None
    opt_out: bool | None = None
    branch_id: int | None = None


class ContactResponse(BaseModel):
    id: int
    church_id: int
    branch_id: int
    first_name: str
    last_name: str
    phone: str
    email: str | None
    gender: str | None
    age_group: str | None
    address: str | None
    category: str
    source: str | None
    status: str
    assigned_worker_id: int | None
    assigned_worker_name: str | None = None
    branch_name: str | None = None
    foundation_class_status: str | None = None
    foundation_class_start_date: datetime | None = None
    foundation_class_completion_date: datetime | None = None
    baptism_status: str | None = None
    cell_group: str | None = None
    assigned_mentor_id: int | None = None
    assigned_mentor_name: str | None = None
    service_unit_id: int | None = None
    service_unit_name: str | None = None
    service_unit_leader_name: str | None = None
    service_unit_joined_at: datetime | None = None
    unit_active: bool | None = True
    second_visit_date: datetime | None = None
    third_visit_date: datetime | None = None
    last_attendance_date: datetime | None = None
    notes: str | None
    consent_given: bool
    opt_out: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int


class CSVRowResult(BaseModel):
    row: int
    phone: str
    status: str
    message: str
    contact_id: int | None = None


class CSVUploadResponse(BaseModel):
    total_rows: int
    created: int
    skipped: int
    errors: int
    results: list[CSVRowResult]


class DuplicateCheckResponse(BaseModel):
    phone: str
    is_duplicate: bool
    existing_contacts: list[ContactResponse]


class ContactFilter(BaseModel):
    category: str | None = None
    status: str | None = None
    source: str | None = None
    assigned_worker_id: int | None = None
    branch_id: int | None = None
    foundation_class_status: str | None = None
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class JourneyEvent(BaseModel):
    id: str
    type: str
    title: str
    description: str
    date: datetime
    icon: str
    meta: dict[str, str] = {}


class ContactJourneyResponse(BaseModel):
    contact: ContactResponse
    current_stage: str
    first_visit_date: datetime
    assigned_worker_name: str | None
    foundation_class_status: str | None
    service_unit_status: str | None
    follow_up_history: list[JourneyEvent]
    communication_history: list[JourneyEvent]
    timeline: list[JourneyEvent]
