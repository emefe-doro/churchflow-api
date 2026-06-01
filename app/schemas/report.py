from datetime import datetime

from pydantic import BaseModel


class ContactReportItem(BaseModel):
    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    gender: str | None = None
    age_group: str | None = None
    branch_name: str | None = None
    status: str | None = None
    source: str | None = None
    assigned_worker_name: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CategoryReportResponse(BaseModel):
    church_id: int
    category: str
    total: int
    this_week: int
    this_month: int
    page: int
    page_size: int
    total_pages: int
    items: list[ContactReportItem]


class WorkerReportItem(BaseModel):
    worker_id: int | None = None
    worker_name: str | None = None
    branch_name: str | None = None
    role_name: str | None = None
    assigned_contacts: int = 0
    active_contacts: int = 0
    completed_contacts: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    completed_tasks: int = 0
    total_tasks: int = 0


class WorkersReportResponse(BaseModel):
    church_id: int
    total_workers: int
    total_assigned_contacts: int
    total_pending_tasks: int
    total_overdue_tasks: int
    workers: list[WorkerReportItem]


class ServiceUnitReportItem(BaseModel):
    id: int | None = None
    name: str | None = None
    branch_name: str | None = None
    leader_name: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ServiceUnitsReportResponse(BaseModel):
    church_id: int
    total_units: int
    units: list[ServiceUnitReportItem]


class OverdueFollowUpItem(BaseModel):
    task_id: int | None = None
    contact_id: int | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_category: str | None = None
    task_type: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    overdue_days: int = 0
    assigned_worker_name: str | None = None
    notes: str | None = None


class OverdueFollowUpReportResponse(BaseModel):
    church_id: int
    total_overdue: int
    high_priority: int
    medium_priority: int
    low_priority: int
    page: int
    page_size: int
    total_pages: int
    items: list[OverdueFollowUpItem]


class RetentionRate(BaseModel):
    rate: float
    numerator: int
    denominator: int
    label: str


class MonthlyRetention(BaseModel):
    month: str
    first_timer_rate: float
    new_convert_rate: float


class RetentionAnalyticsResponse(BaseModel):
    church_id: int
    first_timer_retention: RetentionRate
    first_timer_conversion: RetentionRate
    new_convert_retention: RetentionRate
    foundation_class_completion: RetentionRate
    monthly_trends: list[MonthlyRetention]


class WorkerPerformanceItem(BaseModel):
    worker_id: int | None = None
    worker_name: str | None = None
    total_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    overdue_rate: float = 0.0
    contacts_assigned: int = 0
    avg_resolution_days: float | None = None


class WorkerPerformanceResponse(BaseModel):
    church_id: int
    overall_completion_rate: float
    overall_overdue_rate: float
    total_tasks: int
    workers: list[WorkerPerformanceItem]


class ServiceUnitGrowthItem(BaseModel):
    unit_id: int | None = None
    unit_name: str | None = None
    contact_count: int = 0
    leader_name: str | None = None


class ServiceUnitGrowthResponse(BaseModel):
    church_id: int
    total_units: int
    total_members_assigned: int
    units: list[ServiceUnitGrowthItem]


class ReturnVisitorData(BaseModel):
    church_id: int
    total_first_timers: int
    returned_once: int
    returned_twice: int
    return_rate: float
    retention_rate: float
