from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact
from app.models.follow_up import CommunicationLog
from app.models.user import User
from app.schemas.communication_log import (
    CommunicationLogCreate,
    CommunicationLogFilter,
    CommunicationLogResponse,
    CommunicationLogUpdate,
)


class CommunicationLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(self, data: CommunicationLogCreate) -> CommunicationLog:
        contact_stmt = select(Contact).where(
            Contact.id == data.contact_id,
            Contact.deleted_at.is_(None),
        )
        result = await self.db.execute(contact_stmt)
        contact = result.scalar_one_or_none()
        if contact is None:
            raise ValueError("Contact not found")

        log = CommunicationLog(
            contact_id=data.contact_id,
            channel=data.channel,
            message=data.message.strip() if data.message else None,
            provider=data.provider.strip() if data.provider else None,
            outcome=data.outcome.strip() if data.outcome else None,
            sent_by=data.sent_by,
            sent_at=data.sent_at,
        )
        self.db.add(log)
        await self.db.flush()

        stmt = (
            select(CommunicationLog)
            .options(
                joinedload(CommunicationLog.contact),
                joinedload(CommunicationLog.sender),
            )
            .where(CommunicationLog.id == log.id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one()

    async def get_log(self, log_id: int) -> CommunicationLog | None:
        stmt = (
            select(CommunicationLog)
            .options(
                joinedload(CommunicationLog.contact),
                joinedload(CommunicationLog.sender),
            )
            .where(CommunicationLog.id == log_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_logs(
        self, church_id: int | None = None, filters: CommunicationLogFilter | None = None
    ) -> tuple[list[CommunicationLog], int]:
        if filters is None:
            filters = CommunicationLogFilter()

        conditions = []
        if church_id is not None:
            conditions.append(Contact.church_id == church_id)
        conditions.append(Contact.deleted_at.is_(None))

        if filters.contact_id is not None:
            conditions.append(CommunicationLog.contact_id == filters.contact_id)
        if filters.channel:
            conditions.append(CommunicationLog.channel == filters.channel)
        if filters.sent_by is not None:
            conditions.append(CommunicationLog.sent_by == filters.sent_by)
        if filters.outcome:
            conditions.append(CommunicationLog.outcome == filters.outcome)
        if filters.date_from:
            conditions.append(CommunicationLog.sent_at >= filters.date_from)
        if filters.date_to:
            conditions.append(CommunicationLog.sent_at <= filters.date_to)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    CommunicationLog.message.ilike(search_term),
                    CommunicationLog.outcome.ilike(search_term),
                )
            )

        where_clause = and_(*conditions)

        count_stmt = (
            select(func.count(CommunicationLog.id))
            .select_from(CommunicationLog)
            .join(Contact, CommunicationLog.contact_id == Contact.id)
            .where(where_clause)
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(CommunicationLog)
            .options(
                joinedload(CommunicationLog.contact),
                joinedload(CommunicationLog.sender),
            )
            .join(Contact, CommunicationLog.contact_id == Contact.id)
            .where(where_clause)
            .order_by(CommunicationLog.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        logs = list(result.unique().scalars().all())

        return logs, total

    async def update_log(self, log_id: int, data: CommunicationLogUpdate) -> CommunicationLog | None:
        log = await self.get_log(log_id)
        if log is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(log, key):
                setattr(log, key, value.strip() if isinstance(value, str) else value)

        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def delete_log(self, log_id: int) -> bool:
        log = await self.get_log(log_id)
        if log is None:
            return False
        await self.db.delete(log)
        await self.db.flush()
        return True

    def _to_response(self, log: CommunicationLog) -> CommunicationLogResponse:
        contact_name = None
        contact_phone = None
        if log.contact:
            contact_name = f"{log.contact.first_name} {log.contact.last_name}"
            contact_phone = log.contact.phone

        worker_name = None
        if log.sender:
            worker_name = log.sender.name

        return CommunicationLogResponse(
            id=log.id,
            contact_id=log.contact_id,
            channel=log.channel,
            message=log.message,
            provider=log.provider,
            outcome=log.outcome,
            status=log.status,
            sent_by=log.sent_by,
            sent_at=log.sent_at,
            contact_name=contact_name,
            contact_phone=contact_phone,
            worker_name=worker_name,
            created_at=log.created_at,
            updated_at=log.updated_at,
        )
