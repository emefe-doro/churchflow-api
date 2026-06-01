import json
import logging

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.models.contact import Contact
from app.models.message_template import MessageTemplate

logger = logging.getLogger(__name__)

PROMPT_TEMPLATES = {
    "first_timer": (
        "Write a warm church welcome message for {name}, who attended {church_name} "
        "on {service_date}. Keep it short, respectful, and suitable for WhatsApp. "
        "Do not add greetings like 'Dear' or subject lines. Just the message body."
    ),
    "new_convert": (
        "Write a caring message for {name}, who recently gave their life to Christ. "
        "Encourage them, invite them to foundation class, and avoid pressure. "
        "Keep it short, respectful, and suitable for WhatsApp. "
        "Do not add greetings like 'Dear' or subject lines. Just the message body."
    ),
    "outreach_convert": (
        "Write a follow-up message for {name}, contacted during outreach at {location}. "
        "Invite them to church and offer support. "
        "Keep it short, respectful, and suitable for WhatsApp. "
        "Do not add greetings like 'Dear' or subject lines. Just the message body."
    ),
    "service_unit": (
        "Write a clear message for {unit_name} about {purpose} on {date}. "
        "Keep it respectful and concise. "
        "Do not add greetings like 'Dear' or subject lines. Just the message body."
    ),
    "general": (
        "Write a warm pastoral follow-up message for {name} from {church_name}. "
        "Keep it short, respectful, and suitable for WhatsApp. "
        "Do not add greetings like 'Dear' or subject lines. Just the message body."
    ),
}

TONE_MODIFIERS = {
    "warm": "Make the message warm and welcoming.",
    "caring": "Make the message caring and compassionate.",
    "encouraging": "Make the message encouraging and uplifting.",
    "formal": "Use formal and respectful language.",
    "concise": "Keep the message very concise and to the point.",
    "pastoral": "Use a gentle pastoral tone.",
}

TEMPLATE_FALLBACKS = {
    "first_timer": ["first_timer", "general"],
    "new_convert": ["new_convert", "general"],
    "outreach_convert": ["outreach", "general"],
    "service_unit": ["service_unit", "general"],
    "general": ["general"],
}


class AIDraftService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_draft(
        self,
        contact_id: int,
        category: str,
        channel: str,
        branch_id: int,
        church_id: int,
        tone: str | None = None,
        additional_context: str | None = None,
        override_prompt: str | None = None,
    ) -> tuple[str, bool, str | None, int | None, int | None]:
        contact = await self._get_contact(contact_id, church_id)
        if contact is None:
            raise ValueError("Contact not found or does not belong to this church")

        context = await self._build_context(contact, category, branch_id)

        ai_body = None
        token_count = None
        template_id = None
        template_name = None

        if settings.AI_API_KEY:
            try:
                ai_body, token_count = await self._call_ai_api(
                    category=category,
                    context=context,
                    tone=tone,
                    additional_context=additional_context,
                    override_prompt=override_prompt,
                )
            except Exception as exc:
                logger.warning("AI draft failed: %s", exc)

        if ai_body:
            return ai_body, False, template_name, template_id, token_count

        if not settings.AI_FALLBACK_TO_TEMPLATE:
            raise RuntimeError("AI draft unavailable and template fallback is disabled")

        template_body, template_id = await self._get_template_fallback(
            contact, category, church_id
        )

        if template_body is None:
            raise RuntimeError("No AI response and no approved templates available")

        template_name = "fallback"
        populated = self._populate_template(template_body, context)
        return populated, True, template_name, template_id, None

    async def _build_context(self, contact: Contact, category: str, branch_id: int) -> dict:
        church_name = "our church"
        service_date = "recently"
        location = "the outreach"
        unit_name = "the service unit"

        if contact.church:
            church_name = contact.church.name

        if contact.source == "outreach" and contact.notes:
            location = contact.notes[:100] or location

        context = {
            "name": f"{contact.first_name} {contact.last_name}",
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "church_name": church_name,
            "service_date": service_date,
            "location": location,
            "unit_name": unit_name or "the service unit",
            "purpose": "the upcoming assignment",
            "date": "the next service",
            "category": contact.category,
            "source": contact.source or "unknown",
            "status": contact.status,
            "phone": contact.phone,
        }

        return context

    async def _call_ai_api(
        self,
        category: str,
        context: dict,
        tone: str | None = None,
        additional_context: str | None = None,
        override_prompt: str | None = None,
    ) -> tuple[str, int | None]:
        if override_prompt:
            system_prompt = override_prompt.format(**context)
        else:
            template = PROMPT_TEMPLATES.get(category, PROMPT_TEMPLATES["general"])
            system_prompt = template.format(**context)

        if tone and tone in TONE_MODIFIERS:
            system_prompt = f"{system_prompt} {TONE_MODIFIERS[tone]}"

        if additional_context:
            system_prompt = f"{system_prompt}\n\nAdditional context: {additional_context}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a pastoral assistant for a church. Write warm, respectful, "
                    "and concise messages. Never use Dear or formal letter greetings. "
                    "Return only the message body, no explanation."
                ),
            },
            {"role": "user", "content": system_prompt},
        ]

        request_body = {
            "model": settings.AI_MODEL,
            "messages": messages,
            "max_tokens": settings.AI_MAX_TOKENS,
            "temperature": settings.AI_TEMPERATURE,
        }

        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }

        chat_url = f"{settings.AI_API_BASE_URL}/chat/completions"
        if settings.AI_PROVIDER == "deepseek":
            chat_url = f"{settings.AI_API_BASE_URL}/v1/chat/completions"

        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = await client.post(chat_url, json=request_body, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        token_count = data.get("usage", {}).get("total_tokens")

        if not content:
            raise ValueError("AI returned empty response")

        return content, token_count

    async def _get_template_fallback(
        self, contact: Contact, category: str, church_id: int
    ) -> tuple[str | None, int | None]:
        fallback_categories = TEMPLATE_FALLBACKS.get(category, ["general"])

        stmt = (
            select(MessageTemplate)
            .where(
                and_(
                    MessageTemplate.church_id == church_id,
                    MessageTemplate.approved.is_(True),
                    MessageTemplate.category.in_(fallback_categories),
                )
            )
            .order_by(MessageTemplate.category.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()
        if template:
            return template.body, template.id

        stmt = (
            select(MessageTemplate)
            .where(
                and_(
                    MessageTemplate.church_id == church_id,
                    MessageTemplate.approved.is_(True),
                )
            )
            .order_by(MessageTemplate.category.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()
        if template:
            return template.body, template.id

        return None, None

    def _populate_template(self, template_body: str, context: dict) -> str:
        body = template_body
        for key, value in context.items():
            body = body.replace(f"{{{key}}}", str(value))
        for key in ["church_name", "first_name", "last_name", "name", "location",
                     "unit_name", "purpose", "date"]:
            body = body.replace(f"{{{key}}}", str(context.get(key, "")))
        return body

    async def _get_contact(self, contact_id: int, church_id: int) -> Contact | None:
        from app.models.church import Church, Branch

        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.church).load_only(Church.id, Church.name),
                joinedload(Contact.branch).load_only(Branch.id, Branch.name),
            )
            .where(
                Contact.id == contact_id,
                Contact.church_id == church_id,
                Contact.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()
