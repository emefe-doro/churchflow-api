from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.whatsapp import WhatsAppMessage, WhatsAppQueueItem
from app.schemas.whatsapp import (
    WhatsAppQueueItemResponse,
    WhatsAppQueueStatusResponse,
)


class WhatsAppQueueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_queue_status(self) -> WhatsAppQueueStatusResponse:
        from sqlalchemy import func

        stmt = select(
            func.count(WhatsAppQueueItem.id),
            WhatsAppQueueItem.status,
        ).group_by(WhatsAppQueueItem.status)

        result = await self.db.execute(stmt)
        rows = result.all()

        counts = {row[1]: row[0] for row in rows}
        return WhatsAppQueueStatusResponse(
            pending=counts.get("pending", 0),
            processing=counts.get("processing", 0),
            completed=counts.get("completed", 0),
            failed=counts.get("failed", 0),
            total=sum(counts.values()),
        )

    async def get_queue_item(self, queue_item_id: int) -> WhatsAppQueueItem | None:
        stmt = select(WhatsAppQueueItem).where(WhatsAppQueueItem.id == queue_item_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_items(self, limit: int = 10) -> list[WhatsAppQueueItem]:
        stmt = (
            select(WhatsAppQueueItem)
            .where(
                WhatsAppQueueItem.status == "pending",
                (
                    (WhatsAppQueueItem.next_attempt_at.is_(None))
                    | (WhatsAppQueueItem.next_attempt_at <= datetime.now(timezone.utc))
                ),
            )
            .order_by(WhatsAppQueueItem.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_processing(self, queue_item_id: int) -> WhatsAppQueueItem | None:
        item = await self.get_queue_item(queue_item_id)
        if item is None:
            return None

        item.status = "processing"
        item.attempt_count += 1
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def mark_completed(
        self, queue_item_id: int, external_message_id: str | None = None
    ) -> WhatsAppQueueItem | None:
        item = await self.get_queue_item(queue_item_id)
        if item is None:
            return None

        item.status = "completed"
        if external_message_id:
            item.external_message_id = external_message_id
            message_stmt = select(WhatsAppMessage).where(WhatsAppMessage.id == item.message_id)
            msg_result = await self.db.execute(message_stmt)
            message = msg_result.scalar_one_or_none()
            if message:
                message.external_message_id = external_message_id

        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def mark_failed(
        self, queue_item_id: int, error: str
    ) -> WhatsAppQueueItem | None:
        item = await self.get_queue_item(queue_item_id)
        if item is None:
            return None

        from app.config import settings

        item.last_error = error
        if item.attempt_count >= item.max_attempts:
            item.status = "failed"
            message_stmt = select(WhatsAppMessage).where(WhatsAppMessage.id == item.message_id)
            msg_result = await self.db.execute(message_stmt)
            message = msg_result.scalar_one_or_none()
            if message:
                message.status = "failed"
        else:
            item.status = "pending"
            item.next_attempt_at = datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp() + settings.WHATSAPP_RETRY_DELAY_SECONDS,
                tz=timezone.utc,
            )

        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_message_queue_items(self, message_id: int) -> list[WhatsAppQueueItem]:
        stmt = (
            select(WhatsAppQueueItem)
            .where(WhatsAppQueueItem.message_id == message_id)
            .order_by(WhatsAppQueueItem.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _to_response(self, item: WhatsAppQueueItem) -> WhatsAppQueueItemResponse:
        return WhatsAppQueueItemResponse(
            id=item.id,
            message_id=item.message_id,
            status=item.status,
            attempt_count=item.attempt_count,
            max_attempts=item.max_attempts,
            next_attempt_at=item.next_attempt_at,
            last_error=item.last_error,
            external_message_id=item.external_message_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
