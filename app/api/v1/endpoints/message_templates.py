from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.message_template import (
    TemplateCreate,
    TemplateFilter,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.message_template import MessageTemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(data: TemplateCreate, db: AsyncSession = Depends(get_db)):
    service = MessageTemplateService(db)
    return service._to_response(await service.create_template(data))


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    category: str | None = Query(None),
    channel: str | None = Query(None),
    approved: bool | None = Query(None),
    branch_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TemplateFilter(
        category=category,
        channel=channel,
        approved=approved,
        branch_id=branch_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = MessageTemplateService(db)
    templates, total = await service.get_templates(church_id, filters)
    return TemplateListResponse(
        items=[service._to_response(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/first-timer", response_model=TemplateListResponse)
async def list_first_timer_templates(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TemplateFilter(category="first_timer", channel=channel, page=page, page_size=page_size)
    service = MessageTemplateService(db)
    templates, total = await service.get_templates(church_id, filters)
    return TemplateListResponse(
        items=[service._to_response(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/new-convert", response_model=TemplateListResponse)
async def list_new_convert_templates(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TemplateFilter(category="new_convert", channel=channel, page=page, page_size=page_size)
    service = MessageTemplateService(db)
    templates, total = await service.get_templates(church_id, filters)
    return TemplateListResponse(
        items=[service._to_response(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/outreach", response_model=TemplateListResponse)
async def list_outreach_templates(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TemplateFilter(category="outreach", channel=channel, page=page, page_size=page_size)
    service = MessageTemplateService(db)
    templates, total = await service.get_templates(church_id, filters)
    return TemplateListResponse(
        items=[service._to_response(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/service-unit", response_model=TemplateListResponse)
async def list_service_unit_templates(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TemplateFilter(category="service_unit", channel=channel, page=page, page_size=page_size)
    service = MessageTemplateService(db)
    templates, total = await service.get_templates(church_id, filters)
    return TemplateListResponse(
        items=[service._to_response(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/general", response_model=TemplateListResponse)
async def list_general_templates(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TemplateFilter(category="general", channel=channel, page=page, page_size=page_size)
    service = MessageTemplateService(db)
    templates, total = await service.get_templates(church_id, filters)
    return TemplateListResponse(
        items=[service._to_response(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = MessageTemplateService(db)
    template = await service.get_template(template_id, church_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return service._to_response(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = MessageTemplateService(db)
    template = await service.update_template(template_id, data, church_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return service._to_response(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = MessageTemplateService(db)
    deleted = await service.delete_template(template_id, church_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")


@router.put("/{template_id}/approve", response_model=TemplateResponse)
async def approve_template(
    template_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = MessageTemplateService(db)
    template = await service.approve_template(template_id, church_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return service._to_response(template)


@router.put("/{template_id}/unapprove", response_model=TemplateResponse)
async def unapprove_template(
    template_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = MessageTemplateService(db)
    template = await service.unapprove_template(template_id, church_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return service._to_response(template)
