from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.follow_up import (
    TaskAssign,
    TaskCreate,
    TaskFilter,
    TaskListResponse,
    TaskNotes,
    TaskPriority,
    TaskResponse,
    TaskUpdate,
)
from app.services.follow_up import FollowUpService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/detect-overdue")
async def detect_overdue(
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    count = await service.detect_overdue_tasks(church_id)
    return {"marked_overdue": count}


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    try:
        task = await service.create_task(data, church_id)
        return service._to_response(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    contact_id: int | None = Query(None),
    assigned_to: int | None = Query(None),
    task_type: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    due_date_from: str | None = Query(None),
    due_date_to: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TaskFilter(
        contact_id=contact_id,
        assigned_to=assigned_to,
        task_type=task_type,
        status=status,
        priority=priority,
        due_date_from=datetime.fromisoformat(due_date_from) if due_date_from else None,
        due_date_to=datetime.fromisoformat(due_date_to) if due_date_to else None,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = FollowUpService(db)
    tasks, total = await service.get_tasks(church_id, filters)
    return TaskListResponse(
        items=[service._to_response(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/overdue", response_model=TaskListResponse)
async def list_overdue_tasks(
    db: AsyncSession = Depends(get_db),
    church_id: int = Query(..., description="Church ID"),
    assigned_to: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = TaskFilter(
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )
    service = FollowUpService(db)
    tasks, total = await service.get_overdue_tasks(church_id, filters)
    return TaskListResponse(
        items=[service._to_response(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    task = await service.get_task(task_id, church_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service._to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    task = await service.update_task(task_id, data, church_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service._to_response(task)


@router.put("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    data: TaskAssign,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    task = await service.assign_task(task_id, data, church_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service._to_response(task)


@router.put("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    task = await service.complete_task(task_id, church_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service._to_response(task)


@router.put("/{task_id}/notes", response_model=TaskResponse)
async def update_task_notes(
    task_id: int,
    data: TaskNotes,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    task = await service.update_task_notes(task_id, data, church_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service._to_response(task)


@router.put("/{task_id}/priority", response_model=TaskResponse)
async def update_task_priority(
    task_id: int,
    data: TaskPriority,
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = FollowUpService(db)
    task = await service.update_task_priority(task_id, data, church_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return service._to_response(task)
