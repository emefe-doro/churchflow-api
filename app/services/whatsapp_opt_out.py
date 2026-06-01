from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact
from app.models.whatsapp import WhatsAppOptOut
from app.schemas.whatsapp import (
    WhatsAppOptOutCreate,
    WhatsAppOptOutFilter,
    WhatsAppOptOutResponse,
)


class WhatsAppOptOutService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_opt_out(
        self, data: WhatsAppOptOutCreate, church_id: int
    ) -> WhatsAppOptOut:
        normalized = data.phone_number.strip().lstrip("+")

        existing_stmt = select(WhatsAppOptOut).where(
            WhatsAppOptOut.church_id == church_id,
            (
                (WhatsAppOptOut.phone_number == data.phone_number)
                | (WhatsAppOptOut.phone_number == f"+{normalized}")
                | (WhatsAppOptOut.phone_number == normalized)
            ),
        )
        existing_result = await self.db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.reason = data.reason or existing.reason
            existing.source = data.source
            existing.opted_out_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        contact_id = data.contact_id
        if contact_id:
            contact_stmt = select(Contact).where(
                Contact.id == contact_id,
                Contact.church_id == church_id,
            )
            contact_result = await self.db.execute(contact_stmt)
            contact = contact_result.scalar_one_or_none()
            if contact:
                contact.opt_out = True

        opt_out = WhatsAppOptOut(
            church_id=church_id,
            contact_id=contact_id,
            phone_number=data.phone_number,
            reason=data.reason,
            source=data.source,
            opted_out_at=datetime.now(timezone.utc),
        )
        self.db.add(opt_out)
        await self.db.flush()
        await self.db.refresh(opt_out)
        return opt_out

    async def is_opted_out(self, phone_number: str, church_id: int) -> bool:
        normalized = phone_number.strip().lstrip("+")

        stmt = select(WhatsAppOptOut).where(
            WhatsAppOptOut.church_id == church_id,
            (
                (WhatsAppOptOut.phone_number == phone_number)
                | (WhatsAppOptOut.phone_number == f"+{normalized}")
                | (WhatsAppOptOut.phone_number == normalized)
            ),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_opt_out(self, opt_out_id: int, church_id: int) -> WhatsAppOptOut | None:
        stmt = (
            select(WhatsAppOptOut)
            .options(joinedload(WhatsAppOptOut.contact))
            .where(
                WhatsAppOptOut.id == opt_out_id,
                WhatsAppOptOut.church_id == church_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_opt_outs(
        self, church_id: int, filters: WhatsAppOptOutFilter | None = None
    ) -> tuple[list[WhatsAppOptOut], int]:
        if filters is None:
            filters = WhatsAppOptOutFilter()

        conditions = [WhatsAppOptOut.church_id == church_id]

        if filters.phone_number:
            conditions.append(WhatsAppOptOut.phone_number.contains(filters.phone_number))
        if filters.contact_id is not None:
            conditions.append(WhatsAppOptOut.contact_id == filters.contact_id)
        if filters.source:
            conditions.append(WhatsAppOptOut.source == filters.source)

        where_clause = and_(*conditions)

        count_stmt = select(func.count(WhatsAppOptOut.id)).where(where_clause)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(WhatsAppOptOut)
            .options(joinedload(WhatsAppOptOut.contact))
            .where(where_clause)
            .order_by(WhatsAppOptOut.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.unique().scalars().all())
        return items, total

    def _to_response(self, opt_out: WhatsAppOptOut) -> WhatsAppOptOutResponse:
        contact_name = None
        if opt_out.contact:
            contact_name = f"{opt_out.contact.first_name} {opt_out.contact.last_name}"

        return WhatsAppOptOutResponse(
            id=opt_out.id,
            church_id=opt_out.church_id,
            contact_id=opt_out.contact_id,
            phone_number=opt_out.phone_number,
            reason=opt_out.reason,
            source=opt_out.source,
            opted_out_at=opt_out.opted_out_at,
            contact_name=contact_name,
            created_at=opt_out.created_at,
            updated_at=opt_out.updated_at,
        )
