from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.report import (
    CategoryReportResponse,
    OverdueFollowUpReportResponse,
    RetentionAnalyticsResponse,
    ReturnVisitorData,
    ServiceUnitGrowthResponse,
    ServiceUnitsReportResponse,
    WorkerPerformanceResponse,
    WorkersReportResponse,
)
from app.services.report import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/first-timers", response_model=CategoryReportResponse)
async def first_timers_report(
    church_id: int = Query(..., description="Church ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    date_from: Optional[datetime] = Query(None, description="Filter contacts created from date"),
    date_to: Optional[datetime] = Query(None, description="Filter contacts created to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_category_report(
        church_id=church_id,
        category="first_timer",
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/new-converts", response_model=CategoryReportResponse)
async def new_converts_report(
    church_id: int = Query(..., description="Church ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    date_from: Optional[datetime] = Query(None, description="Filter contacts created from date"),
    date_to: Optional[datetime] = Query(None, description="Filter contacts created to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_category_report(
        church_id=church_id,
        category="new_convert",
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/outreach-converts", response_model=CategoryReportResponse)
async def outreach_converts_report(
    church_id: int = Query(..., description="Church ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    date_from: Optional[datetime] = Query(None, description="Filter contacts created from date"),
    date_to: Optional[datetime] = Query(None, description="Filter contacts created to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_category_report(
        church_id=church_id,
        category="outreach_convert",
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/workers", response_model=WorkersReportResponse)
async def workers_report(
    church_id: int = Query(..., description="Church ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_workers_report(church_id=church_id, branch_id=branch_id)


@router.get("/service-units", response_model=ServiceUnitsReportResponse)
async def service_units_report(
    church_id: int = Query(..., description="Church ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_service_units_report(church_id=church_id, branch_id=branch_id)


@router.get("/overdue-follow-ups", response_model=OverdueFollowUpReportResponse)
async def overdue_follow_ups_report(
    church_id: int = Query(..., description="Church ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_overdue_followups_report(
        church_id=church_id,
        branch_id=branch_id,
        page=page,
        page_size=page_size,
    )


@router.get("/analytics/retention", response_model=RetentionAnalyticsResponse)
async def retention_analytics(
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_retention_analytics(church_id)


@router.get("/analytics/worker-performance", response_model=WorkerPerformanceResponse)
async def worker_performance_analytics(
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_worker_performance(church_id)


@router.get("/analytics/service-unit-growth", response_model=ServiceUnitGrowthResponse)
async def service_unit_growth_analytics(
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_service_unit_growth(church_id)


@router.get("/return-visitors", response_model=ReturnVisitorData)
async def return_visitors_report(
    church_id: int = Query(..., description="Church ID"),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_return_visitor_report(church_id)
