from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowFilter,
    WorkflowResponse,
    WorkflowUpdate,
)


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(self, data: WorkflowCreate) -> Workflow:
        workflow = Workflow(
            church_id=data.church_id,
            branch_id=data.branch_id,
            name=data.name.strip(),
            trigger_event=data.trigger_event,
            target_category=data.target_category,
            active=data.active,
            rules_json=data.rules_json,
        )
        self.db.add(workflow)
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: int, church_id: int | None = None) -> Workflow | None:
        stmt = (
            select(Workflow)
            .options(joinedload(Workflow.branch))
            .where(Workflow.id == workflow_id)
        )
        if church_id is not None:
            stmt = stmt.where(Workflow.church_id == church_id)
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_workflows(
        self, church_id: int, filters: WorkflowFilter | None = None
    ) -> tuple[list[Workflow], int]:
        if filters is None:
            filters = WorkflowFilter()

        conditions = [Workflow.church_id == church_id]

        if filters.trigger_event:
            conditions.append(Workflow.trigger_event == filters.trigger_event)
        if filters.target_category:
            conditions.append(Workflow.target_category == filters.target_category)
        if filters.active is not None:
            conditions.append(Workflow.active == filters.active)
        if filters.branch_id is not None:
            conditions.append(Workflow.branch_id == filters.branch_id)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(Workflow.name.ilike(search_term))

        where_clause = and_(*conditions)

        count_stmt = select(func.count(Workflow.id)).where(where_clause)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(Workflow)
            .options(joinedload(Workflow.branch))
            .where(where_clause)
            .order_by(Workflow.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        workflows = list(result.unique().scalars().all())

        return workflows, total

    async def update_workflow(
        self, workflow_id: int, data: WorkflowUpdate, church_id: int
    ) -> Workflow | None:
        workflow = await self.get_workflow(workflow_id, church_id)
        if workflow is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(workflow, key):
                setattr(workflow, key, value.strip() if isinstance(value, str) else value)

        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def delete_workflow(self, workflow_id: int, church_id: int) -> bool:
        workflow = await self.get_workflow(workflow_id, church_id)
        if workflow is None:
            return False
        await self.db.delete(workflow)
        await self.db.flush()
        return True

    async def toggle_workflow(self, workflow_id: int, church_id: int) -> Workflow | None:
        workflow = await self.get_workflow(workflow_id, church_id)
        if workflow is None:
            return None
        workflow.active = not workflow.active
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    def _to_response(self, workflow: Workflow) -> WorkflowResponse:
        branch_name = None
        if workflow.branch:
            branch_name = workflow.branch.name

        return WorkflowResponse(
            id=workflow.id,
            church_id=workflow.church_id,
            branch_id=workflow.branch_id,
            name=workflow.name,
            trigger_event=workflow.trigger_event,
            target_category=workflow.target_category,
            active=workflow.active,
            rules_json=workflow.rules_json,
            branch_name=branch_name,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
        )
