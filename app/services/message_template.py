from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.message_template import MessageTemplate
from app.schemas.message_template import (
    TemplateCreate,
    TemplateFilter,
    TemplateResponse,
    TemplateUpdate,
)


class MessageTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(self, data: TemplateCreate) -> MessageTemplate:
        template = MessageTemplate(
            church_id=data.church_id,
            branch_id=data.branch_id,
            name=data.name.strip(),
            category=data.category,
            channel=data.channel,
            body=data.body.strip(),
            approved=False,
            created_by=data.created_by,
        )
        self.db.add(template)
        await self.db.flush()
        stmt = (
            select(MessageTemplate)
            .options(joinedload(MessageTemplate.creator), joinedload(MessageTemplate.branch))
            .where(MessageTemplate.id == template.id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one()

    async def get_template(self, template_id: int, church_id: int | None = None) -> MessageTemplate | None:
        stmt = (
            select(MessageTemplate)
            .options(
                joinedload(MessageTemplate.creator),
                joinedload(MessageTemplate.branch),
            )
            .where(MessageTemplate.id == template_id)
        )
        if church_id is not None:
            stmt = stmt.where(MessageTemplate.church_id == church_id)
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_templates(
        self, church_id: int, filters: TemplateFilter | None = None
    ) -> tuple[list[MessageTemplate], int]:
        if filters is None:
            filters = TemplateFilter()

        conditions = [MessageTemplate.church_id == church_id]

        if filters.category:
            conditions.append(MessageTemplate.category == filters.category)
        if filters.channel:
            conditions.append(MessageTemplate.channel == filters.channel)
        if filters.approved is not None:
            conditions.append(MessageTemplate.approved == filters.approved)
        if filters.branch_id is not None:
            conditions.append(MessageTemplate.branch_id == filters.branch_id)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    MessageTemplate.name.ilike(search_term),
                    MessageTemplate.body.ilike(search_term),
                )
            )

        where_clause = and_(*conditions)

        count_stmt = select(func.count(MessageTemplate.id)).where(where_clause)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(MessageTemplate)
            .options(
                joinedload(MessageTemplate.creator),
                joinedload(MessageTemplate.branch),
            )
            .where(where_clause)
            .order_by(MessageTemplate.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        templates = list(result.unique().scalars().all())

        return templates, total

    async def update_template(
        self, template_id: int, data: TemplateUpdate, church_id: int
    ) -> MessageTemplate | None:
        template = await self.get_template(template_id, church_id)
        if template is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value.strip() if isinstance(value, str) else value)

        await self.db.flush()
        return await self.get_template(template_id, church_id)

    async def delete_template(self, template_id: int, church_id: int) -> bool:
        template = await self.get_template(template_id, church_id)
        if template is None:
            return False
        await self.db.delete(template)
        await self.db.flush()
        return True

    async def approve_template(self, template_id: int, church_id: int) -> MessageTemplate | None:
        template = await self.get_template(template_id, church_id)
        if template is None:
            return None
        template.approved = True
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def unapprove_template(self, template_id: int, church_id: int) -> MessageTemplate | None:
        template = await self.get_template(template_id, church_id)
        if template is None:
            return None
        template.approved = False
        await self.db.flush()
        await self.db.refresh(template)
        return template

    def _to_response(self, template: MessageTemplate) -> TemplateResponse:
        creator_name = None
        if template.creator:
            creator_name = template.creator.name

        branch_name = None
        if template.branch:
            branch_name = template.branch.name

        return TemplateResponse(
            id=template.id,
            church_id=template.church_id,
            branch_id=template.branch_id,
            name=template.name,
            category=template.category,
            channel=template.channel,
            body=template.body,
            approved=template.approved,
            created_by=template.created_by,
            creator_name=creator_name,
            branch_name=branch_name,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
