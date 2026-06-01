from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactFilter, ContactListResponse, ContactResponse

router = APIRouter(prefix="/foundation-class", tags=["foundation-class"])

STATUSES = ["not_started", "invited", "attending", "completed"]


@router.get("")
async def list_foundation_class(
    church_id: int = Query(..., description="Church ID"),
    status: str | None = Query(None, description="Filter by foundation class status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from app.services.contact import ContactService

    filters = ContactFilter(
        foundation_class_status=status,
        page=page,
        page_size=page_size,
        search=search,
    )
    service = ContactService(db)
    contacts, total = await service.get_contacts(church_id, filters)

    stats = {}
    for s in STATUSES:
        stmt = select(func.count(Contact.id)).where(
            Contact.church_id == church_id,
            Contact.foundation_class_status == s,
            Contact.deleted_at.is_(None),
        )
        count = (await db.execute(stmt)).scalar() or 0
        stats[s] = count

    return {
        "church_id": church_id,
        "stats": stats,
        "items": [service._to_response(c) for c in contacts],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size) if total > 0 else 1,
    }
