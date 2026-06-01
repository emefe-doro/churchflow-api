from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact
from app.models.follow_up import FollowUpTask
from app.models.user import User
from app.schemas.follow_up import (
    TaskAssign,
    TaskCreate,
    TaskFilter,
    TaskNotes,
    TaskPriority,
    TaskResponse,
    TaskUpdate,
)


class FollowUpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_overdue_tasks(self, church_id: int) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            select(FollowUpTask)
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(
                Contact.church_id == church_id,
                Contact.deleted_at.is_(None),
                FollowUpTask.due_date.isnot(None),
                FollowUpTask.due_date < now,
                FollowUpTask.status.in_(["pending", "in_progress"]),
            )
        )
        result = await self.db.execute(stmt)
        overdue_tasks = list(result.scalars().all())

        for task in overdue_tasks:
            task.status = "overdue"
            self.db.add(task)

        if overdue_tasks:
            await self.db.flush()

        return len(overdue_tasks)

    async def create_task(self, data: TaskCreate, church_id: int) -> FollowUpTask:
        contact_stmt = select(Contact).where(
            Contact.id == data.contact_id,
            Contact.church_id == church_id,
            Contact.deleted_at.is_(None),
        )
        result = await self.db.execute(contact_stmt)
        contact = result.scalar_one_or_none()
        if contact is None:
            raise ValueError("Contact not found or does not belong to this church")

        task = FollowUpTask(
            contact_id=data.contact_id,
            assigned_to=data.assigned_to,
            task_type=data.task_type,
            due_date=data.due_date,
            status="pending",
            priority=data.priority,
            notes=data.notes.strip() if data.notes else None,
        )
        self.db.add(task)
        await self.db.flush()
        stmt = (
            select(FollowUpTask)
            .options(
                joinedload(FollowUpTask.contact),
                joinedload(FollowUpTask.assigned_user),
            )
            .where(FollowUpTask.id == task.id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one()

    async def get_task(self, task_id: int, church_id: int) -> FollowUpTask | None:
        stmt = (
            select(FollowUpTask)
            .options(
                joinedload(FollowUpTask.contact),
                joinedload(FollowUpTask.assigned_user),
            )
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(
                FollowUpTask.id == task_id,
                Contact.church_id == church_id,
                Contact.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_tasks(
        self, church_id: int, filters: TaskFilter | None = None
    ) -> tuple[list[FollowUpTask], int]:
        if filters is None:
            filters = TaskFilter()

        await self.detect_overdue_tasks(church_id)

        conditions = [
            Contact.church_id == church_id,
            Contact.deleted_at.is_(None),
        ]

        if filters.contact_id is not None:
            conditions.append(FollowUpTask.contact_id == filters.contact_id)
        if filters.assigned_to is not None:
            conditions.append(FollowUpTask.assigned_to == filters.assigned_to)
        if filters.task_type:
            conditions.append(FollowUpTask.task_type == filters.task_type)
        if filters.status:
            conditions.append(FollowUpTask.status == filters.status)
        if filters.priority:
            conditions.append(FollowUpTask.priority == filters.priority)
        if filters.due_date_from:
            conditions.append(FollowUpTask.due_date >= filters.due_date_from)
        if filters.due_date_to:
            conditions.append(FollowUpTask.due_date <= filters.due_date_to)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    FollowUpTask.notes.ilike(search_term),
                )
            )

        where_clause = and_(*conditions)

        count_stmt = (
            select(func.count(FollowUpTask.id))
            .select_from(FollowUpTask)
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(where_clause)
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(FollowUpTask)
            .options(
                joinedload(FollowUpTask.contact),
                joinedload(FollowUpTask.assigned_user),
            )
            .join(Contact, FollowUpTask.contact_id == Contact.id)
            .where(where_clause)
            .order_by(FollowUpTask.due_date.asc().nullslast(), FollowUpTask.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        tasks = list(result.unique().scalars().all())

        return tasks, total

    async def get_overdue_tasks(
        self, church_id: int, filters: TaskFilter | None = None
    ) -> tuple[list[FollowUpTask], int]:
        if filters is None:
            filters = TaskFilter()
        filters.status = "overdue"
        return await self.get_tasks(church_id, filters)

    async def update_task(
        self, task_id: int, data: TaskUpdate, church_id: int
    ) -> FollowUpTask | None:
        task = await self.get_task(task_id, church_id)
        if task is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value.strip() if isinstance(value, str) else value)

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def assign_task(
        self, task_id: int, data: TaskAssign, church_id: int
    ) -> FollowUpTask | None:
        task = await self.get_task(task_id, church_id)
        if task is None:
            return None

        task.assigned_to = data.assigned_to
        if task.status == "pending":
            task.status = "in_progress"
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def complete_task(self, task_id: int, church_id: int) -> FollowUpTask | None:
        task = await self.get_task(task_id, church_id)
        if task is None:
            return None

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update_task_notes(
        self, task_id: int, data: TaskNotes, church_id: int
    ) -> FollowUpTask | None:
        task = await self.get_task(task_id, church_id)
        if task is None:
            return None

        task.notes = data.notes.strip()
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update_task_priority(
        self, task_id: int, data: TaskPriority, church_id: int
    ) -> FollowUpTask | None:
        task = await self.get_task(task_id, church_id)
        if task is None:
            return None

        task.priority = data.priority
        await self.db.flush()
        await self.db.refresh(task)
        return task

    def _to_response(self, task: FollowUpTask) -> TaskResponse:
        contact_name = None
        if task.contact:
            contact_name = f"{task.contact.first_name} {task.contact.last_name}"

        assigned_user_name = None
        if task.assigned_user:
            assigned_user_name = task.assigned_user.name

        return TaskResponse(
            id=task.id,
            contact_id=task.contact_id,
            assigned_to=task.assigned_to,
            task_type=task.task_type,
            due_date=task.due_date,
            status=task.status,
            priority=task.priority,
            notes=task.notes,
            completed_at=task.completed_at,
            contact_name=contact_name,
            assigned_user_name=assigned_user_name,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
