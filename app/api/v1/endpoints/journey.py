from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.contact import ContactJourneyResponse
from app.services.contact import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/{contact_id}/journey", response_model=ContactJourneyResponse)
async def get_contact_journey(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ContactService(db)
    journey = await service.get_contact_journey(contact_id, church_id)
    if journey is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return journey
