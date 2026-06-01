from datetime import datetime

from pydantic import BaseModel, Field


class ServiceUnitCreate(BaseModel):
    church_id: int
    branch_id: int
    name: str = Field(min_length=1, max_length=200)
    leader_id: int | None = None


class ServiceUnitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    leader_id: int | None = None
    branch_id: int | None = None


class ServiceUnitResponse(BaseModel):
    id: int
    church_id: int
    branch_id: int
    name: str
    leader_id: int | None = None
    leader_name: str | None = None
    branch_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceUnitListResponse(BaseModel):
    items: list[ServiceUnitResponse]
    total: int
    page: int
    page_size: int


class ServiceUnitMembersResponse(BaseModel):
    unit: ServiceUnitResponse
    member_count: int
    members: list  # filled with ContactResponse at runtime
