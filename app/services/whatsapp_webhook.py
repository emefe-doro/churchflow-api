from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.whatsapp import WhatsAppDeliveryLog, WhatsAppMessage, WhatsAppOptOut
from app.schemas.whatsapp import (
    WhatsAppDeliveryLogListResponse,
    WhatsAppDeliveryLogResponse,
)


class WhatsAppWebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_token(self, mode: str, token: str, challenge: str) -> str | None:
        from app.config import settings

        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            return challenge
        return None

    async def process_webhook(self, payload: dict) -> dict:
        results = {"status_updates": 0, "opt_outs": 0, "errors": 0}

        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                statuses = value.get("statuses", [])
                messages = value.get("messages", [])

                for status in statuses:
                    try:
                        await self._process_status_update(status)
                        results["status_updates"] += 1
                    except Exception:
                        results["errors"] += 1

                for message in messages:
                    try:
                        if await self._process_incoming_message(message, value):
                            results["opt_outs"] += 1
                    except Exception:
                        results["errors"] += 1

        return results

    async def _process_status_update(self, status: dict) -> None:
        external_message_id = status.get("id")
        wa_status = status.get("status")
        timestamp_str = status.get("timestamp")
        errors = status.get("errors", [])

        event_timestamp = None
        if timestamp_str:
            try:
                event_timestamp = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
            except (ValueError, TypeError, OSError):
                pass

        if external_message_id:
            stmt = select(WhatsAppMessage).where(
                WhatsAppMessage.external_message_id == external_message_id
            )
            result = await self.db.execute(stmt)
            message = result.scalar_one_or_none()

            if message:
                mapping = {
                    "sent": "sent",
                    "delivered": "delivered",
                    "read": "read",
                    "failed": "failed",
                    "deleted": "failed",
                }
                new_status = mapping.get(wa_status, "sent")
                if new_status in ("sent", "delivered", "read") and message.status in (
                    "queued",
                    "sent",
                    "delivered",
                ):
                    message.status = new_status

                error_code = None
                error_message = None
                if errors:
                    error_code = str(errors[0].get("code", "")) if errors[0].get("code") else None
                    error_message = errors[0].get("title", "")

                delivery_log = WhatsAppDeliveryLog(
                    message_id=message.id,
                    external_message_id=external_message_id,
                    status=new_status,
                    event_timestamp=event_timestamp,
                    raw_payload=status,
                    error_code=error_code,
                    error_message=error_message,
                )
                self.db.add(delivery_log)

        await self.db.flush()

    async def _process_incoming_message(self, message: dict, value: dict) -> bool:
        text_body = None
        if message.get("type") == "text":
            text_body = message.get("text", {}).get("body", "")

        from_number = message.get("from")
        if not from_number:
            return False

        opt_out_phrases = [
            "stop", "unsubscribe", "opt out", "opt-out", "remove",
            "cancel", "no messages", "don't message", "do not message",
            "quit", "leave",
        ]

        if text_body and any(phrase in text_body.lower() for phrase in opt_out_phrases):
            await self._record_opt_out(
                from_number,
                reason=f"Incoming opt-out message: {text_body[:200]}",
                source="incoming_message",
            )
            return True

        return False

    async def _record_opt_out(
        self, phone_number: str, reason: str | None = None, source: str = "webhook"
    ) -> WhatsAppOptOut:
        normalized = phone_number.strip().lstrip("+")

        existing_stmt = select(WhatsAppOptOut).where(
            (WhatsAppOptOut.phone_number == phone_number)
            | (WhatsAppOptOut.phone_number == f"+{normalized}")
            | (WhatsAppOptOut.phone_number == normalized),
        )
        existing_result = await self.db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            existing.reason = reason or existing.reason
            existing.source = source
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        contact_stmt = select(Contact).where(
            (Contact.phone == phone_number)
            | (Contact.phone == f"+{normalized}")
            | (Contact.phone == normalized),
        )
        contact_result = await self.db.execute(contact_stmt)
        contact = contact_result.scalar_one_or_none()

        church_id = 1
        contact_id = None
        if contact:
            church_id = contact.church_id
            contact_id = contact.id
            contact.opt_out = True

        opt_out = WhatsAppOptOut(
            church_id=church_id,
            contact_id=contact_id,
            phone_number=phone_number,
            reason=reason,
            source=source,
            opted_out_at=datetime.now(timezone.utc),
        )
        self.db.add(opt_out)
        await self.db.flush()
        await self.db.refresh(opt_out)
        return opt_out

    async def get_delivery_logs(
        self, message_id: int
    ) -> tuple[list[WhatsAppDeliveryLog], int]:
        count_stmt = select(WhatsAppDeliveryLog).where(
            WhatsAppDeliveryLog.message_id == message_id
        )
        count_result = await self.db.execute(count_stmt)
        logs = list(count_result.scalars().all())

        stmt = (
            select(WhatsAppDeliveryLog)
            .where(WhatsAppDeliveryLog.message_id == message_id)
            .order_by(WhatsAppDeliveryLog.event_timestamp.desc())
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, len(items)

    def _to_delivery_log_response(self, log: WhatsAppDeliveryLog) -> WhatsAppDeliveryLogResponse:
        return WhatsAppDeliveryLogResponse(
            id=log.id,
            message_id=log.message_id,
            external_message_id=log.external_message_id,
            status=log.status,
            event_timestamp=log.event_timestamp,
            raw_payload=log.raw_payload,
            error_code=log.error_code,
            error_message=log.error_message,
            created_at=log.created_at,
        )

    def _to_delivery_list_response(
        self, items: list[WhatsAppDeliveryLog], total: int
    ) -> WhatsAppDeliveryLogListResponse:
        return WhatsAppDeliveryLogListResponse(
            items=[self._to_delivery_log_response(log) for log in items],
            total=total,
        )
