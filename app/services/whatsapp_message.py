from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact
from app.models.message_template import MessageTemplate
from app.models.whatsapp import WhatsAppMessage, WhatsAppOptOut, WhatsAppQueueItem
from app.schemas.whatsapp import (
    WhatsAppApprovalAction,
    WhatsAppMessageCreate,
    WhatsAppMessageFilter,
    WhatsAppMessageResponse,
    WhatsAppMessageUpdate,
)


class WhatsAppMessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_draft(self, data: WhatsAppMessageCreate, church_id: int, user_id: int) -> WhatsAppMessage:
        contact_stmt = select(Contact).where(
            Contact.id == data.contact_id,
            Contact.church_id == church_id,
            Contact.deleted_at.is_(None),
        )
        result = await self.db.execute(contact_stmt)
        contact = result.scalar_one_or_none()
        if contact is None:
            raise ValueError("Contact not found or does not belong to this church")

        message = WhatsAppMessage(
            church_id=church_id,
            branch_id=data.branch_id,
            contact_id=data.contact_id,
            template_id=data.template_id,
            body=data.body.strip(),
            status="draft",
            priority=data.priority,
            created_by=user_id,
            scheduled_at=data.scheduled_at,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def submit_for_approval(self, message_id: int, church_id: int) -> WhatsAppMessage | None:
        message = await self._get_message(message_id, church_id)
        if message is None:
            return None
        if message.status != "draft":
            raise ValueError(f"Cannot submit message with status '{message.status}' for approval")

        message.status = "pending_approval"
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def approve(
        self, message_id: int, data: WhatsAppApprovalAction, church_id: int, user_id: int
    ) -> WhatsAppMessage | None:
        message = await self._get_message(message_id, church_id)
        if message is None:
            return None

        if data.approved:
            if message.status != "pending_approval":
                raise ValueError(f"Cannot approve message with status '{message.status}'")
            message.status = "approved"
            message.approved_by = user_id
            message.approved_at = datetime.now(timezone.utc)
            message.rejected_reason = None
        else:
            if message.status not in ("pending_approval", "approved"):
                raise ValueError(f"Cannot reject message with status '{message.status}'")
            message.status = "rejected"
            message.approved_by = user_id
            message.rejected_reason = data.rejected_reason

        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def enqueue(self, message_id: int, church_id: int) -> tuple[WhatsAppMessage, WhatsAppQueueItem] | None:
        message = await self._get_message(message_id, church_id)
        if message is None:
            return None
        if message.status != "approved":
            raise ValueError(f"Cannot enqueue message with status '{message.status}'")

        contact_stmt = select(Contact).where(
            Contact.id == message.contact_id,
            Contact.church_id == church_id,
        )
        result = await self.db.execute(contact_stmt)
        contact = result.scalar_one_or_none()

        if contact and contact.opt_out:
            raise ValueError("Contact has opted out of messages")

        opt_out_stmt = select(WhatsAppOptOut).where(
            WhatsAppOptOut.phone_number == (contact.phone if contact else ""),
            WhatsAppOptOut.church_id == church_id,
        )
        opt_out_result = await self.db.execute(opt_out_stmt)
        if opt_out_result.scalar_one_or_none():
            raise ValueError("Phone number has opted out of messages")

        from app.config import settings

        message.status = "queued"
        queue_item = WhatsAppQueueItem(
            message_id=message.id,
            status="pending",
            attempt_count=0,
            max_attempts=settings.WHATSAPP_MAX_RETRY_ATTEMPTS,
        )
        self.db.add(queue_item)
        await self.db.flush()
        await self.db.refresh(message)
        await self.db.refresh(queue_item)
        return message, queue_item

    async def get_message(self, message_id: int, church_id: int) -> WhatsAppMessage | None:
        return await self._get_message(message_id, church_id)

    async def get_messages(
        self, church_id: int, filters: WhatsAppMessageFilter | None = None
    ) -> tuple[list[WhatsAppMessage], int]:
        if filters is None:
            filters = WhatsAppMessageFilter()

        conditions = [WhatsAppMessage.church_id == church_id]

        if filters.contact_id is not None:
            conditions.append(WhatsAppMessage.contact_id == filters.contact_id)
        if filters.status:
            conditions.append(WhatsAppMessage.status == filters.status)
        if filters.priority:
            conditions.append(WhatsAppMessage.priority == filters.priority)
        if filters.template_id is not None:
            conditions.append(WhatsAppMessage.template_id == filters.template_id)
        if filters.created_by is not None:
            conditions.append(WhatsAppMessage.created_by == filters.created_by)
        if filters.scheduled_from:
            conditions.append(WhatsAppMessage.scheduled_at >= filters.scheduled_from)
        if filters.scheduled_to:
            conditions.append(WhatsAppMessage.scheduled_at <= filters.scheduled_to)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(WhatsAppMessage.body.ilike(search_term))

        where_clause = and_(*conditions)

        count_stmt = select(func.count(WhatsAppMessage.id)).where(where_clause)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(WhatsAppMessage)
            .options(
                joinedload(WhatsAppMessage.contact),
                joinedload(WhatsAppMessage.template),
                joinedload(WhatsAppMessage.creator),
                joinedload(WhatsAppMessage.approver),
                joinedload(WhatsAppMessage.branch),
            )
            .where(where_clause)
            .order_by(WhatsAppMessage.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        messages = list(result.unique().scalars().all())
        return messages, total

    async def update_message(
        self, message_id: int, data: WhatsAppMessageUpdate, church_id: int
    ) -> WhatsAppMessage | None:
        message = await self._get_message(message_id, church_id)
        if message is None:
            return None
        if message.status not in ("draft", "rejected"):
            raise ValueError(f"Cannot update message with status '{message.status}'")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(message, key):
                setattr(message, key, value.strip() if isinstance(value, str) else value)

        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def update_status(
        self, message_id: int, church_id: int, status: str, external_message_id: str | None = None
    ) -> WhatsAppMessage | None:
        message = await self._get_message(message_id, church_id)
        if message is None:
            return None

        valid_transitions = {
            "queued": ("approved",),
            "sent": ("queued",),
            "delivered": ("sent",),
            "read": ("sent", "delivered"),
            "failed": ("queued", "sent"),
        }

        allowed = valid_transitions.get(status, ())
        if message.status not in allowed:
            raise ValueError(f"Cannot transition from '{message.status}' to '{status}'")

        message.status = status
        if external_message_id:
            message.external_message_id = external_message_id
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def _get_message(self, message_id: int, church_id: int) -> WhatsAppMessage | None:
        stmt = (
            select(WhatsAppMessage)
            .options(
                joinedload(WhatsAppMessage.contact),
                joinedload(WhatsAppMessage.template),
                joinedload(WhatsAppMessage.creator),
                joinedload(WhatsAppMessage.approver),
                joinedload(WhatsAppMessage.branch),
            )
            .where(
                WhatsAppMessage.id == message_id,
                WhatsAppMessage.church_id == church_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def _to_response(self, message: WhatsAppMessage) -> WhatsAppMessageResponse:
        contact_name = None
        contact_phone = None
        if message.contact:
            contact_name = f"{message.contact.first_name} {message.contact.last_name}"
            contact_phone = message.contact.phone

        template_name = None
        if message.template:
            template_name = message.template.name

        creator_name = None
        if message.creator:
            creator_name = message.creator.name

        approver_name = None
        if message.approver:
            approver_name = message.approver.name

        branch_name = None
        if message.branch:
            branch_name = message.branch.name

        return WhatsAppMessageResponse(
            id=message.id,
            church_id=message.church_id,
            branch_id=message.branch_id,
            contact_id=message.contact_id,
            template_id=message.template_id,
            body=message.body,
            status=message.status,
            priority=message.priority,
            created_by=message.created_by,
            approved_by=message.approved_by,
            approved_at=message.approved_at,
            rejected_reason=message.rejected_reason,
            external_message_id=message.external_message_id,
            scheduled_at=message.scheduled_at,
            contact_name=contact_name,
            contact_phone=contact_phone,
            template_name=template_name,
            creator_name=creator_name,
            approver_name=approver_name,
            branch_name=branch_name,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )
