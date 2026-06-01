from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.communication_log import (
    CommunicationLogCreate,
    CommunicationLogFilter,
    CommunicationLogListResponse,
    CommunicationLogResponse,
    CommunicationLogUpdate,
)
from app.services.communication_log import CommunicationLogService

router = APIRouter(prefix="/communication-logs", tags=["communication-logs"])


@router.post("", response_model=CommunicationLogResponse, status_code=201)
async def create_log(data: CommunicationLogCreate, db: AsyncSession = Depends(get_db)):
    service = CommunicationLogService(db)
    try:
        log = await service.create_log(data)
        return service._to_response(log)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=CommunicationLogListResponse)
async def list_logs(
    db: AsyncSession = Depends(get_db),
    church_id: int | None = Query(None, description="Church ID filter"),
    contact_id: int | None = Query(None),
    channel: str | None = Query(None),
    sent_by: int | None = Query(None),
    outcome: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = CommunicationLogFilter(
        contact_id=contact_id,
        channel=channel,
        sent_by=sent_by,
        outcome=outcome,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = CommunicationLogService(db)
    logs, total = await service.get_logs(church_id, filters)
    return CommunicationLogListResponse(
        items=[service._to_response(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}", response_model=CommunicationLogResponse)
async def get_log(log_id: int, db: AsyncSession = Depends(get_db)):
    service = CommunicationLogService(db)
    log = await service.get_log(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Communication log not found")
    return service._to_response(log)


@router.put("/{log_id}", response_model=CommunicationLogResponse)
async def update_log(log_id: int, data: CommunicationLogUpdate, db: AsyncSession = Depends(get_db)):
    service = CommunicationLogService(db)
    log = await service.update_log(log_id, data)
    if log is None:
        raise HTTPException(status_code=404, detail="Communication log not found")
    return service._to_response(log)


@router.delete("/{log_id}", status_code=204)
async def delete_log(log_id: int, db: AsyncSession = Depends(get_db)):
    service = CommunicationLogService(db)
    deleted = await service.delete_log(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Communication log not found")
