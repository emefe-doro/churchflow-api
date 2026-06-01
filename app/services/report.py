from datetime import datetime, timedelta, timezone
import math

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.church import Branch
from app.models.follow_up import FollowUpTask
from app.models.user import User, Role
from app.models.service_unit import ServiceUnit
from app.schemas.report import (
    CategoryReportResponse,
    ContactReportItem,
    MonthlyRetention,
    OverdueFollowUpItem,
    OverdueFollowUpReportResponse,
    RetentionAnalyticsResponse,
    RetentionRate,
    ServiceUnitGrowthItem,
    ServiceUnitGrowthResponse,
    ServiceUnitReportItem,
    ServiceUnitsReportResponse,
    WorkerPerformanceItem,
    WorkerPerformanceResponse,
    WorkerReportItem,
    WorkersReportResponse,
    ReturnVisitorData,
)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _safe_rate(numerator: int | float, denominator: int | float) -> float:
        try:
            numerator = float(numerator) if not isinstance(numerator, float) else numerator
            denominator = float(denominator) if not isinstance(denominator, float) else denominator
        except (ValueError, TypeError):
            return 0.0
        if denominator <= 0:
            return 0.0
        if numerator < 0 or denominator < 0:
            return 0.0
        if math.isnan(numerator) or math.isnan(denominator):
            return 0.0
        if math.isinf(numerator) or math.isinf(denominator):
            return 0.0
        result = numerator / denominator * 100
        return 0.0 if math.isnan(result) or math.isinf(result) else max(0.0, result)

    @staticmethod
    def _week_range() -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = (monday + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        return monday, sunday

    @staticmethod
    def _month_range() -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
        else:
            last_day = now.replace(month=now.month + 1, day=1) - timedelta(microseconds=1)
        last_day = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        return first_day, last_day

    async def get_category_report(
        self,
        church_id: int,
        category: str,
        branch_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CategoryReportResponse:
        week_start, week_end = self._week_range()
        month_start, month_end = self._month_range()

        base_filter = and_(
            Contact.church_id == church_id,
            Contact.category == category,
            Contact.deleted_at.is_(None),
        )
        if branch_id is not None:
            base_filter = and_(base_filter, Contact.branch_id == branch_id)
        if date_from is not None:
            base_filter = and_(base_filter, Contact.created_at >= date_from)
        if date_to is not None:
            base_filter = and_(base_filter, Contact.created_at <= date_to)

        total = await self.db.scalar(select(func.count(Contact.id)).where(base_filter)) or 0

        week_filter = and_(base_filter, Contact.created_at >= week_start, Contact.created_at <= week_end)
        this_week = await self.db.scalar(select(func.count(Contact.id)).where(week_filter)) or 0

        month_filter = and_(base_filter, Contact.created_at >= month_start, Contact.created_at <= month_end)
        this_month = await self.db.scalar(select(func.count(Contact.id)).where(month_filter)) or 0

        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        offset = (page - 1) * page_size

        items: list[ContactReportItem] = []
        if total > 0:
            stmt = (
                select(
                    Contact,
                    Branch.name.label("branch_name"),
                    User.name.label("assigned_worker_name"),
                )
                .outerjoin(Branch, Contact.branch_id == Branch.id)
                .outerjoin(User, Contact.assigned_worker_id == User.id)
                .where(base_filter)
                .order_by(Contact.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(stmt)
            for row in result.all():
                c, branch_name, worker_name = row
                items.append(
                    ContactReportItem(
                        id=c.id,
                        first_name=c.first_name,
                        last_name=c.last_name,
                        phone=c.phone,
                        email=c.email,
                        gender=c.gender,
                        age_group=c.age_group,
                        branch_name=branch_name,
                        status=c.status,
                        source=c.source,
                        assigned_worker_name=worker_name,
                        created_at=c.created_at,
                    )
                )

        return CategoryReportResponse(
            church_id=church_id,
            category=category,
            total=total,
            this_week=this_week,
            this_month=this_month,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items,
        )

    async def get_workers_report(
        self,
        church_id: int,
        branch_id: int | None = None,
    ) -> WorkersReportResponse:
        user_filter = and_(User.church_id == church_id, User.active.is_(True))
        if branch_id is not None:
            user_filter = and_(user_filter, User.branch_id == branch_id)

        worker_ids_result = await self.db.execute(select(User.id).where(user_filter))
        worker_ids = [r[0] for r in worker_ids_result.all()]

        workers_data: list[WorkerReportItem] = []
        total_assigned = 0
        total_pending = 0
        total_overdue = 0

        for wid in worker_ids:
            user_result = await self.db.execute(
                select(
                    User.name,
                    Branch.name.label("branch_name"),
                    Role.name.label("role_name"),
                )
                .outerjoin(Branch, User.branch_id == Branch.id)
                .outerjoin(Role, User.role_id == Role.id)
                .where(User.id == wid)
            )
            user_row = user_result.first()
            if not user_row:
                continue
            user_name, branch_name, role_name = user_row

            assigned_contacts = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id,
                        Contact.assigned_worker_id == wid,
                        Contact.deleted_at.is_(None),
                    )
                )
            ) or 0

            active_contacts = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id,
                        Contact.assigned_worker_id == wid,
                        Contact.status.in_(["new", "contacted", "follow_up", "attending"]),
                        Contact.deleted_at.is_(None),
                    )
                )
            ) or 0

            completed_contacts = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id,
                        Contact.assigned_worker_id == wid,
                        Contact.status == "completed",
                        Contact.deleted_at.is_(None),
                    )
                )
            ) or 0

            pending_tasks = await self.db.scalar(
                select(func.count(FollowUpTask.id)).where(
                    and_(
                        FollowUpTask.assigned_to == wid,
                        FollowUpTask.status.in_(["pending", "in_progress"]),
                    )
                )
            ) or 0

            overdue_tasks = await self.db.scalar(
                select(func.count(FollowUpTask.id)).where(
                    and_(
                        FollowUpTask.assigned_to == wid,
                        FollowUpTask.status == "overdue",
                    )
                )
            ) or 0

            completed_tasks = await self.db.scalar(
                select(func.count(FollowUpTask.id)).where(
                    and_(
                        FollowUpTask.assigned_to == wid,
                        FollowUpTask.status == "completed",
                    )
                )
            ) or 0

            total = pending_tasks + overdue_tasks + completed_tasks
            total_assigned += assigned_contacts
            total_pending += pending_tasks
            total_overdue += overdue_tasks

            workers_data.append(
                WorkerReportItem(
                    worker_id=wid,
                    worker_name=user_name,
                    branch_name=branch_name,
                    role_name=role_name,
                    assigned_contacts=assigned_contacts,
                    active_contacts=active_contacts,
                    completed_contacts=completed_contacts,
                    pending_tasks=pending_tasks,
                    overdue_tasks=overdue_tasks,
                    completed_tasks=completed_tasks,
                    total_tasks=total,
                )
            )

        return WorkersReportResponse(
            church_id=church_id,
            total_workers=len(workers_data),
            total_assigned_contacts=total_assigned,
            total_pending_tasks=total_pending,
            total_overdue_tasks=total_overdue,
            workers=workers_data,
        )

    async def get_service_units_report(
        self,
        church_id: int,
        branch_id: int | None = None,
    ) -> ServiceUnitsReportResponse:
        unit_filter = and_(ServiceUnit.church_id == church_id)
        if branch_id is not None:
            unit_filter = and_(unit_filter, ServiceUnit.branch_id == branch_id)

        total_units = await self.db.scalar(select(func.count(ServiceUnit.id)).where(unit_filter)) or 0

        stmt = (
            select(
                ServiceUnit,
                Branch.name.label("branch_name"),
                User.name.label("leader_name"),
            )
            .outerjoin(Branch, ServiceUnit.branch_id == Branch.id)
            .outerjoin(User, ServiceUnit.leader_id == User.id)
            .where(unit_filter)
            .order_by(ServiceUnit.name)
        )
        result = await self.db.execute(stmt)

        units: list[ServiceUnitReportItem] = []
        for row in result.all():
            su, branch_name, leader_name = row
            units.append(
                ServiceUnitReportItem(
                    id=su.id,
                    name=su.name,
                    branch_name=branch_name,
                    leader_name=leader_name,
                    created_at=su.created_at,
                )
            )

        return ServiceUnitsReportResponse(
            church_id=church_id,
            total_units=total_units,
            units=units,
        )

    async def get_overdue_followups_report(
        self,
        church_id: int,
        branch_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OverdueFollowUpReportResponse:
        base_filter = and_(
            FollowUpTask.status == "overdue",
        )

        contact_filter = and_(
            Contact.church_id == church_id,
            Contact.deleted_at.is_(None),
        )
        if branch_id is not None:
            contact_filter = and_(contact_filter, Contact.branch_id == branch_id)

        total_overdue = await self.db.scalar(
            select(func.count(FollowUpTask.id))
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(and_(base_filter, contact_filter))
        ) or 0

        high_priority = await self.db.scalar(
            select(func.count(FollowUpTask.id))
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(and_(base_filter, contact_filter, FollowUpTask.priority == "high"))
        ) or 0

        medium_priority = await self.db.scalar(
            select(func.count(FollowUpTask.id))
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(and_(base_filter, contact_filter, FollowUpTask.priority == "medium"))
        ) or 0

        low_priority = await self.db.scalar(
            select(func.count(FollowUpTask.id))
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(and_(base_filter, contact_filter, FollowUpTask.priority == "low"))
        ) or 0

        total_pages = max(1, (total_overdue + page_size - 1) // page_size) if total_overdue > 0 else 1
        offset = (page - 1) * page_size

        items: list[OverdueFollowUpItem] = []
        now = datetime.now(timezone.utc)

        if total_overdue > 0:
            stmt = (
                select(
                    FollowUpTask,
                    Contact.id.label("contact_id"),
                    (Contact.first_name + " " + Contact.last_name).label("contact_name"),
                    Contact.phone.label("contact_phone"),
                    Contact.category.label("contact_category"),
                    User.name.label("assigned_worker_name"),
                )
                .join(Contact, FollowUpTask.contact_id == Contact.id)
                .outerjoin(User, FollowUpTask.assigned_to == User.id)
                .where(and_(base_filter, contact_filter))
                .order_by(FollowUpTask.priority.desc(), FollowUpTask.due_date.asc())
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(stmt)
            for row in result.all():
                t, cid, cname, cphone, ccat, wname = row
                overdue_days = 0
                if t.due_date:
                    delta = now - t.due_date
                    overdue_days = delta.days
                items.append(
                    OverdueFollowUpItem(
                        task_id=t.id,
                        contact_id=cid,
                        contact_name=cname,
                        contact_phone=cphone,
                        contact_category=ccat,
                        task_type=t.task_type,
                        priority=t.priority,
                        due_date=t.due_date,
                        overdue_days=overdue_days,
                        assigned_worker_name=wname,
                        notes=t.notes,
                    )
                )

        return OverdueFollowUpReportResponse(
            church_id=church_id,
            total_overdue=total_overdue,
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items,
        )

    async def get_retention_analytics(self, church_id: int) -> RetentionAnalyticsResponse:
        total_first_timers = await self.db.scalar(
            select(func.count(Contact.id)).where(
                and_(Contact.church_id == church_id, Contact.category == "first_timer", Contact.deleted_at.is_(None))
            )
        ) or 0

        converted_first_timers = await self.db.scalar(
            select(func.count(Contact.id)).where(
                and_(
                    Contact.church_id == church_id,
                    Contact.category == "first_timer",
                    Contact.status.in_(["attending", "completed"]),
                    Contact.deleted_at.is_(None),
                )
            )
        ) or 0

        new_converts_from_ft = await self.db.scalar(
            select(func.count(Contact.id)).where(
                and_(
                    Contact.church_id == church_id,
                    Contact.category == "new_convert",
                    Contact.deleted_at.is_(None),
                )
            )
        ) or 0

        total_new_converts = new_converts_from_ft

        retained_new_converts = await self.db.scalar(
            select(func.count(Contact.id)).where(
                and_(
                    Contact.church_id == church_id,
                    Contact.category == "new_convert",
                    Contact.status.in_(["attending", "completed"]),
                    Contact.deleted_at.is_(None),
                )
            )
        ) or 0

        foundation_enrolled = await self.db.scalar(
            select(func.count(Contact.id)).where(
                and_(
                    Contact.church_id == church_id,
                    Contact.category == "new_convert",
                    Contact.foundation_class_status.in_(["invited", "attending", "completed"]),
                    Contact.deleted_at.is_(None),
                )
            )
        ) or 0

        foundation_completed = await self.db.scalar(
            select(func.count(Contact.id)).where(
                and_(
                    Contact.church_id == church_id,
                    Contact.category == "new_convert",
                    Contact.foundation_class_status == "completed",
                    Contact.deleted_at.is_(None),
                )
            )
        ) or 0

        ft_retention_rate = self._safe_rate(converted_first_timers, total_first_timers)
        ft_conversion_rate = self._safe_rate(new_converts_from_ft, total_first_timers)
        nc_retention_rate = self._safe_rate(retained_new_converts, total_new_converts)
        fc_completion_rate = self._safe_rate(foundation_completed, foundation_enrolled)

        monthly_trends: list[MonthlyRetention] = []
        for i in range(5, -1, -1):
            month_start = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30 * i)
            if i == 0:
                month_end = datetime.now(timezone.utc)
            else:
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(microseconds=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(microseconds=1)
            month_label = month_start.strftime("%b")

            month_ft_total = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id, Contact.category == "first_timer",
                        Contact.created_at <= month_end, Contact.deleted_at.is_(None),
                    )
                )
            ) or 0
            month_ft_retained = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id, Contact.category == "first_timer",
                        Contact.status.in_(["attending", "completed"]),
                        Contact.created_at <= month_end, Contact.deleted_at.is_(None),
                    )
                )
            ) or 0
            month_nc_total = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id, Contact.category == "new_convert",
                        Contact.created_at <= month_end, Contact.deleted_at.is_(None),
                    )
                )
            ) or 0
            month_nc_retained = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id, Contact.category == "new_convert",
                        Contact.status.in_(["attending", "completed"]),
                        Contact.created_at <= month_end, Contact.deleted_at.is_(None),
                    )
                )
            ) or 0

            monthly_trends.append(MonthlyRetention(
                month=month_label,
                first_timer_rate=round(self._safe_rate(month_ft_retained, month_ft_total), 1),
                new_convert_rate=round(self._safe_rate(month_nc_retained, month_nc_total), 1),
            ))

        return RetentionAnalyticsResponse(
            church_id=church_id,
            first_timer_retention=RetentionRate(
                rate=round(ft_retention_rate, 1),
                numerator=converted_first_timers,
                denominator=total_first_timers,
                label="First timers who are attending/completed",
            ),
            first_timer_conversion=RetentionRate(
                rate=round(ft_conversion_rate, 1),
                numerator=new_converts_from_ft,
                denominator=total_first_timers,
                label="First timers who became new converts",
            ),
            new_convert_retention=RetentionRate(
                rate=round(nc_retention_rate, 1),
                numerator=retained_new_converts,
                denominator=total_new_converts,
                label="New converts who are attending/completed",
            ),
            foundation_class_completion=RetentionRate(
                rate=round(fc_completion_rate, 1),
                numerator=foundation_completed,
                denominator=foundation_enrolled,
                label="Enrolled new converts who completed foundation class",
            ),
            monthly_trends=monthly_trends,
        )

    async def get_worker_performance(self, church_id: int) -> WorkerPerformanceResponse:
        users_result = await self.db.execute(
            select(User.id, User.name).where(and_(User.church_id == church_id, User.active.is_(True)))
        )
        users = users_result.all()

        workers: list[WorkerPerformanceItem] = []
        total_completed = 0
        total_tasks_all = 0
        total_overdue = 0

        for uid, uname in users:
            completed = await self.db.scalar(
                select(func.count(FollowUpTask.id)).where(
                    and_(FollowUpTask.assigned_to == uid, FollowUpTask.status == "completed")
                )
            ) or 0
            overdue = await self.db.scalar(
                select(func.count(FollowUpTask.id)).where(
                    and_(FollowUpTask.assigned_to == uid, FollowUpTask.status == "overdue")
                )
            ) or 0
            pending = await self.db.scalar(
                select(func.count(FollowUpTask.id)).where(
                    and_(FollowUpTask.assigned_to == uid, FollowUpTask.status.in_(["pending", "in_progress"]))
                )
            ) or 0
            contacts = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id,
                        Contact.assigned_worker_id == uid,
                        Contact.deleted_at.is_(None),
                    )
                )
            ) or 0

            task_total = completed + overdue + pending
            if task_total == 0 and contacts == 0:
                continue

            completion_rate = round(self._safe_rate(completed, task_total), 1)
            overdue_rate = round(self._safe_rate(overdue, task_total), 1)

            avg_days = None
            if completed > 0:
                avg_result = await self.db.execute(
                    select(
                        func.avg(
                            (FollowUpTask.completed_at - FollowUpTask.created_at) / 86400.0
                        )
                    ).where(
                        and_(
                            FollowUpTask.assigned_to == uid,
                            FollowUpTask.status == "completed",
                            FollowUpTask.completed_at.isnot(None),
                        )
                    )
                )
                avg_val = avg_result.scalar()
                avg_days = round(float(avg_val), 1) if avg_val is not None else None

            total_completed += completed
            total_tasks_all += task_total
            total_overdue += overdue

            workers.append(WorkerPerformanceItem(
                worker_id=uid,
                worker_name=uname,
                total_tasks=task_total,
                completed_tasks=completed,
                overdue_tasks=overdue,
                completion_rate=completion_rate,
                overdue_rate=overdue_rate,
                contacts_assigned=contacts,
                avg_resolution_days=avg_days,
            ))

        workers.sort(key=lambda w: w.completion_rate, reverse=True)

        return WorkerPerformanceResponse(
            church_id=church_id,
            overall_completion_rate=round(self._safe_rate(total_completed, total_tasks_all), 1),
            overall_overdue_rate=round(self._safe_rate(total_overdue, total_tasks_all), 1),
            total_tasks=total_tasks_all,
            workers=workers,
        )

    async def get_service_unit_growth(self, church_id: int) -> ServiceUnitGrowthResponse:
        units_result = await self.db.execute(
            select(ServiceUnit.id, ServiceUnit.name, User.name.label("leader_name"))
            .outerjoin(User, ServiceUnit.leader_id == User.id)
            .where(ServiceUnit.church_id == church_id)
            .order_by(ServiceUnit.name)
        )
        units_data = units_result.all()

        units: list[ServiceUnitGrowthItem] = []
        total_members = 0

        for uid, uname, leader_name in units_data:
            member_count = await self.db.scalar(
                select(func.count(Contact.id)).where(
                    and_(
                        Contact.church_id == church_id,
                        Contact.deleted_at.is_(None),
                        Contact.service_unit_id == uid,
                    )
                )
            ) or 0

            total_members += member_count
            units.append(ServiceUnitGrowthItem(
                unit_id=uid,
                unit_name=uname,
                contact_count=member_count,
                leader_name=leader_name,
            ))

        units.sort(key=lambda u: u.contact_count, reverse=True)

        return ServiceUnitGrowthResponse(
            church_id=church_id,
            total_units=len(units),
            total_members_assigned=total_members,
            units=units,
        )

    async def get_return_visitor_report(self, church_id: int) -> ReturnVisitorData:
        total_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.church_id == church_id,
                Contact.category == "first_timer",
                Contact.deleted_at.is_(None),
            )
        )
        total = (await self.db.execute(total_stmt)).scalar() or 0

        returned_once_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.church_id == church_id,
                Contact.category == "first_timer",
                Contact.second_visit_date.isnot(None),
                Contact.deleted_at.is_(None),
            )
        )
        returned_once = (await self.db.execute(returned_once_stmt)).scalar() or 0

        returned_twice_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.church_id == church_id,
                Contact.category == "first_timer",
                Contact.third_visit_date.isnot(None),
                Contact.deleted_at.is_(None),
            )
        )
        returned_twice = (await self.db.execute(returned_twice_stmt)).scalar() or 0

        retained_stmt = select(func.count(Contact.id)).where(
            and_(
                Contact.church_id == church_id,
                Contact.category == "first_timer",
                Contact.status.in_(["attending", "completed"]),
                Contact.deleted_at.is_(None),
            )
        )
        retained = (await self.db.execute(retained_stmt)).scalar() or 0

        return ReturnVisitorData(
            church_id=church_id,
            total_first_timers=total,
            returned_once=returned_once,
            returned_twice=returned_twice,
            return_rate=round(self._safe_rate(returned_once, total), 1),
            retention_rate=round(self._safe_rate(retained, total), 1),
        )
