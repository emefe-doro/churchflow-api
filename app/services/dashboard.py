from datetime import datetime, timedelta, timezone
import math

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact
from app.models.follow_up import FollowUpTask
from app.models.user import User
from app.schemas.dashboard import DashboardResponse, WorkerSummaryItem
from app.services.follow_up import FollowUpService


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _week_range() -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = (monday + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        return monday, sunday

    async def get_dashboard(self, church_id: int) -> DashboardResponse:
        follow_up_svc = FollowUpService(self.db)
        await follow_up_svc.detect_overdue_tasks(church_id)

        week_start, week_end = self._week_range()

        pending_count, overdue_count, completed_count = await self._task_counts(church_id)
        first_timers_count = await self._contacts_count(church_id, "first_timer", week_start, week_end)
        new_converts_count = await self._contacts_count(church_id, "new_convert", week_start, week_end)
        worker_summary = await self._worker_summary(church_id)
        total_ft, return_rate, retention_rate = await self._return_stats(church_id)

        return DashboardResponse(
            church_id=church_id,
            pending_tasks=pending_count,
            overdue_tasks=overdue_count,
            completed_tasks=completed_count,
            first_timers_this_week=first_timers_count,
            new_converts_this_week=new_converts_count,
            total_first_timers=total_ft,
            return_rate=round(return_rate, 1),
            retention_rate=round(retention_rate, 1),
            worker_summary=worker_summary,
        )

    async def _task_counts(self, church_id: int) -> tuple[int, int, int]:
        status_case = case(
            (FollowUpTask.status.in_(["pending", "in_progress"]), "pending"),
            (FollowUpTask.status == "completed", "completed"),
            (FollowUpTask.status == "overdue", "overdue"),
            else_=None,
        ).label("category")

        stmt = (
            select(
                status_case,
                func.count(FollowUpTask.id),
            )
            .select_from(FollowUpTask)
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(
                Contact.church_id == church_id,
                Contact.deleted_at.is_(None),
            )
            .group_by(status_case)
        )
        result = await self.db.execute(stmt)
        rows = {row[0]: row[1] for row in result.all() if row[0] is not None}
        return rows.get("pending", 0), rows.get("overdue", 0), rows.get("completed", 0)

    async def _contacts_count(
        self, church_id: int, category: str, date_from: datetime, date_to: datetime
    ) -> int:
        stmt = select(func.count(Contact.id)).where(
            Contact.church_id == church_id,
            Contact.category == category,
            Contact.created_at >= date_from,
            Contact.created_at <= date_to,
            Contact.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _worker_summary(self, church_id: int) -> list[WorkerSummaryItem]:
        pending_case = case(
            (FollowUpTask.status.in_(["pending", "in_progress"]), 1),
            else_=0,
        )
        completed_case = case(
            (FollowUpTask.status == "completed", 1),
            else_=0,
        )
        overdue_case = case(
            (FollowUpTask.status == "overdue", 1),
            else_=0,
        )

        stmt = (
            select(
                FollowUpTask.assigned_to,
                func.sum(pending_case).label("pending"),
                func.sum(completed_case).label("completed"),
                func.sum(overdue_case).label("overdue"),
                func.count(FollowUpTask.id).label("total"),
            )
            .select_from(FollowUpTask)
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(
                Contact.church_id == church_id,
                Contact.deleted_at.is_(None),
                FollowUpTask.assigned_to.isnot(None),
            )
            .group_by(FollowUpTask.assigned_to)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        worker_ids = [row[0] for row in rows]
        users_stmt = select(User.id, User.name).where(User.id.in_(worker_ids))
        users_result = await self.db.execute(users_stmt)
        user_map = {u.id: u.name for u in users_result.all()}

        return [
            WorkerSummaryItem(
                worker_id=worker_id or 0,
                worker_name=user_map.get(worker_id, "Unknown"),
                total_tasks=total or 0,
                pending=pending or 0,
                completed=completed or 0,
                overdue=overdue or 0,
            )
            for worker_id, pending, completed, overdue, total in rows
        ]

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

    async def _return_stats(self, church_id: int) -> tuple[int, float, float]:
        total_stmt = select(func.count(Contact.id)).where(
            Contact.church_id == church_id,
            Contact.category == "first_timer",
            Contact.deleted_at.is_(None),
        )
        total = (await self.db.execute(total_stmt)).scalar() or 0

        returned_stmt = select(func.count(Contact.id)).where(
            Contact.church_id == church_id,
            Contact.category == "first_timer",
            Contact.second_visit_date.isnot(None),
            Contact.deleted_at.is_(None),
        )
        returned = (await self.db.execute(returned_stmt)).scalar() or 0

        retained_stmt = select(func.count(Contact.id)).where(
            Contact.church_id == church_id,
            Contact.category == "first_timer",
            Contact.status.in_(["attending", "completed"]),
            Contact.deleted_at.is_(None),
        )
        retained = (await self.db.execute(retained_stmt)).scalar() or 0

        return total, self._safe_rate(returned, total), self._safe_rate(retained, total)
