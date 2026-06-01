from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowFilter,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(data: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    service = WorkflowService(db)
    return service._to_response(await service.create_workflow(data))


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    trigger_event: str | None = Query(None),
    target_category: str | None = Query(None),
    active: bool | None = Query(None),
    branch_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event=trigger_event,
        target_category=target_category,
        active=active,
        branch_id=branch_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/first-timer-created", response_model=WorkflowListResponse)
async def list_first_timer_created(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event="contact_created",
        target_category="first_timer",
        active=active,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/new-convert-created", response_model=WorkflowListResponse)
async def list_new_convert_created(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event="contact_created",
        target_category="new_convert",
        active=active,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/outreach-convert-created", response_model=WorkflowListResponse)
async def list_outreach_convert_created(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event="contact_created",
        target_category="outreach_convert",
        active=active,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/no-response", response_model=WorkflowListResponse)
async def list_no_response_workflows(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    target_category: str | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event="no_response",
        target_category=target_category,
        active=active,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/task-completed", response_model=WorkflowListResponse)
async def list_task_completed_workflows(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    target_category: str | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event="task_completed",
        target_category=target_category,
        active=active,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/overdue", response_model=WorkflowListResponse)
async def list_overdue_workflows(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    target_category: str | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = WorkflowFilter(
        trigger_event="overdue",
        target_category=target_category,
        active=active,
        page=page,
        page_size=page_size,
    )
    service = WorkflowService(db)
    workflows, total = await service.get_workflows(church_id, filters)
    return WorkflowListResponse(
        items=[service._to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id, church_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return service._to_response(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    data: WorkflowUpdate,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    workflow = await service.update_workflow(workflow_id, data, church_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return service._to_response(workflow)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    deleted = await service.delete_workflow(workflow_id, church_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.put("/{workflow_id}/toggle", response_model=WorkflowResponse)
async def toggle_workflow(
    workflow_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    workflow = await service.toggle_workflow(workflow_id, church_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return service._to_response(workflow)
