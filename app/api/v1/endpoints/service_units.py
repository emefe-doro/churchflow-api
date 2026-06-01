from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.service_unit import (
    ServiceUnitCreate,
    ServiceUnitListResponse,
    ServiceUnitMembersResponse,
    ServiceUnitResponse,
    ServiceUnitUpdate,
)
from app.services.service_unit import ServiceUnitService

router = APIRouter(prefix="/service-units", tags=["service-units"])


@router.post("", response_model=ServiceUnitResponse, status_code=201)
async def create_service_unit(data: ServiceUnitCreate, db: AsyncSession = Depends(get_db)):
    service = ServiceUnitService(db)
    return service._to_response(await service.create_unit(data))


@router.get("", response_model=ServiceUnitListResponse)
async def list_service_units(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    branch_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    service = ServiceUnitService(db)
    units, total = await service.list_units(church_id, branch_id, page, page_size)
    return ServiceUnitListResponse(
        items=[service._to_response(u) for u in units],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{unit_id}", response_model=ServiceUnitResponse)
async def get_service_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ServiceUnitService(db)
    unit = await service.get_unit(unit_id, church_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Service unit not found")
    return service._to_response(unit)


@router.put("/{unit_id}", response_model=ServiceUnitResponse)
async def update_service_unit(
    unit_id: int,
    data: ServiceUnitUpdate,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ServiceUnitService(db)
    unit = await service.update_unit(unit_id, data, church_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Service unit not found")
    return service._to_response(unit)


@router.delete("/{unit_id}", status_code=204)
async def delete_service_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ServiceUnitService(db)
    deleted = await service.delete_unit(unit_id, church_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service unit not found")


@router.get("/{unit_id}/members", response_model=ServiceUnitMembersResponse)
async def get_unit_members(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ServiceUnitService(db)
    result = await service.get_members(unit_id, church_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Service unit not found")
    return result


@router.get("/leader/{leader_id}", response_model=list[ServiceUnitResponse])
async def get_leader_units(
    leader_id: int,
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
):
    service = ServiceUnitService(db)
    return await service.get_units_by_leader(leader_id, church_id)
