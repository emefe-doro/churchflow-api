from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.contact import (
    ContactCreate,
    ContactFilter,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
    CSVUploadResponse,
    DuplicateCheckResponse,
)
from app.schemas.follow_up import TaskCreate
from app.services.contact import ContactService
from app.services.follow_up import FollowUpService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(data: ContactCreate, db: AsyncSession = Depends(get_db)):
    service = ContactService(db)
    contact = await service.create_contact(data)

    if data.category == "first_timer":
        follow_up_service = FollowUpService(db)
        task_data = TaskCreate(
            contact_id=contact.id,
            assigned_to=data.assigned_worker_id if data.assigned_worker_id else None,
            task_type="message",
            due_date=datetime.now(timezone.utc) + timedelta(hours=24),
            priority="high",
            notes="Send welcome message to first-time visitor — auto-generated follow-up",
        )
        await follow_up_service.create_task(task_data, data.church_id)

    return service._to_response(contact)


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    category: str | None = Query(None),
    status: str | None = Query(None),
    source: str | None = Query(None),
    assigned_worker_id: int | None = Query(None),
    branch_id: int | None = Query(None),
    search: str | None = Query(None),
    foundation_class_status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    from datetime import datetime

    filters = ContactFilter(
        category=category,
        status=status,
        source=source,
        assigned_worker_id=assigned_worker_id,
        branch_id=branch_id,
        foundation_class_status=foundation_class_status,
        search=search,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        page=page,
        page_size=page_size,
    )
    service = ContactService(db)
    contacts, total = await service.get_contacts(church_id, filters)
    return ContactListResponse(
        items=[service._to_response(c) for c in contacts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/first-timers", response_model=ContactListResponse)
async def list_first_timers(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
):
    filters = ContactFilter(page=page, page_size=page_size, search=search)
    service = ContactService(db)
    contacts, total = await service.get_first_timers(church_id, filters)
    return ContactListResponse(
        items=[service._to_response(c) for c in contacts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/new-converts", response_model=ContactListResponse)
async def list_new_converts(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
):
    filters = ContactFilter(page=page, page_size=page_size, search=search)
    service = ContactService(db)
    contacts, total = await service.get_new_converts(church_id, filters)
    return ContactListResponse(
        items=[service._to_response(c) for c in contacts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/outreach-converts", response_model=ContactListResponse)
async def list_outreach_converts(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
):
    filters = ContactFilter(page=page, page_size=page_size, search=search)
    service = ContactService(db)
    contacts, total = await service.get_outreach_converts(church_id, filters)
    return ContactListResponse(
        items=[service._to_response(c) for c in contacts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate_phone(
    church_id: int = Query(..., description="Church ID"),
    phone: str = Query(..., description="Phone number to check"),
    exclude_contact_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    return await service.check_duplicate_phone(church_id, phone, exclude_contact_id)


@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_csv(
    church_id: int = Query(..., description="Church ID"),
    branch_id: int = Query(..., description="Branch ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    service = ContactService(db)
    try:
        return await service.upload_csv(church_id, branch_id, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int | None = Query(None),
):
    service = ContactService(db)
    contact = await service.get_contact(contact_id, church_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return service._to_response(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ContactService(db)
    contact = await service.update_contact(contact_id, data, church_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return service._to_response(contact)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ContactService(db)
    deleted = await service.delete_contact(contact_id, church_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
