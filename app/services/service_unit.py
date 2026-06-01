from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.service_unit import ServiceUnit
from app.models.contact import Contact
from app.models.user import User
from app.schemas.service_unit import (
    ServiceUnitCreate,
    ServiceUnitListResponse,
    ServiceUnitMembersResponse,
    ServiceUnitResponse,
    ServiceUnitUpdate,
)
from app.schemas.contact import ContactResponse


class ServiceUnitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_unit(self, data: ServiceUnitCreate) -> ServiceUnit:
        unit = ServiceUnit(
            church_id=data.church_id,
            branch_id=data.branch_id,
            name=data.name.strip(),
            leader_id=data.leader_id,
        )
        self.db.add(unit)
        await self.db.flush()

        stmt = (
            select(ServiceUnit)
            .options(joinedload(ServiceUnit.leader), joinedload(ServiceUnit.branch))
            .where(ServiceUnit.id == unit.id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one()

    async def get_unit(self, unit_id: int, church_id: int) -> ServiceUnit | None:
        stmt = (
            select(ServiceUnit)
            .options(joinedload(ServiceUnit.leader), joinedload(ServiceUnit.branch))
            .where(ServiceUnit.id == unit_id, ServiceUnit.church_id == church_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_units(
        self, church_id: int, branch_id: int | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[ServiceUnit], int]:
        conditions = [ServiceUnit.church_id == church_id]
        if branch_id is not None:
            conditions.append(ServiceUnit.branch_id == branch_id)

        count_stmt = select(func.count(ServiceUnit.id)).where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(ServiceUnit)
            .options(joinedload(ServiceUnit.leader), joinedload(ServiceUnit.branch))
            .where(and_(*conditions))
            .order_by(ServiceUnit.name)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all()), total

    async def update_unit(self, unit_id: int, data: ServiceUnitUpdate, church_id: int) -> ServiceUnit | None:
        unit = await self.get_unit(unit_id, church_id)
        if unit is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(unit, key):
                setattr(unit, key, value.strip() if isinstance(value, str) else value)
        await self.db.flush()
        await self.db.refresh(unit)
        return unit

    async def delete_unit(self, unit_id: int, church_id: int) -> bool:
        unit = await self.get_unit(unit_id, church_id)
        if unit is None:
            return False
        await self.db.delete(unit)
        await self.db.flush()
        return True

    async def get_members(self, unit_id: int, church_id: int) -> ServiceUnitMembersResponse | None:
        unit = await self.get_unit(unit_id, church_id)
        if unit is None:
            return None

        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.assigned_worker),
                joinedload(Contact.branch),
                joinedload(Contact.service_unit).joinedload(ServiceUnit.leader),
            )
            .where(
                Contact.service_unit_id == unit_id,
                Contact.church_id == church_id,
                Contact.deleted_at.is_(None),
            )
            .order_by(Contact.last_name, Contact.first_name)
        )
        result = await self.db.execute(stmt)
        members = list(result.unique().scalars().all())

        contact_svc = _make_contact_response

        return ServiceUnitMembersResponse(
            unit=self._to_response(unit),
            member_count=len(members),
            members=[contact_svc(m) for m in members],
        )

    async def get_units_by_leader(
        self, leader_id: int, church_id: int
    ) -> list[ServiceUnitResponse]:
        stmt = (
            select(ServiceUnit)
            .options(joinedload(ServiceUnit.leader), joinedload(ServiceUnit.branch))
            .where(
                ServiceUnit.leader_id == leader_id,
                ServiceUnit.church_id == church_id,
            )
            .order_by(ServiceUnit.name)
        )
        result = await self.db.execute(stmt)
        units = list(result.unique().scalars().all())
        return [self._to_response(u) for u in units]

    def _to_response(self, unit: ServiceUnit) -> ServiceUnitResponse:
        leader_name = unit.leader.name if unit.leader else None
        branch_name = unit.branch.name if unit.branch else None
        return ServiceUnitResponse(
            id=unit.id,
            church_id=unit.church_id,
            branch_id=unit.branch_id,
            name=unit.name,
            leader_id=unit.leader_id,
            leader_name=leader_name,
            branch_name=branch_name,
            created_at=unit.created_at,
            updated_at=unit.updated_at,
        )


def _make_contact_response(contact: Contact) -> ContactResponse:
    worker_name = contact.assigned_worker.name if contact.assigned_worker else None
    branch_name = contact.branch.name if contact.branch else None
    service_unit_name = contact.service_unit.name if contact.service_unit else None
    service_unit_leader_name = None
    if contact.service_unit and contact.service_unit.leader:
        service_unit_leader_name = contact.service_unit.leader.name
    return ContactResponse(
        id=contact.id,
        church_id=contact.church_id,
        branch_id=contact.branch_id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        phone=contact.phone,
        email=contact.email,
        gender=contact.gender,
        age_group=contact.age_group,
        address=contact.address,
        category=contact.category,
        source=contact.source,
        status=contact.status,
        assigned_worker_id=contact.assigned_worker_id,
        assigned_worker_name=worker_name,
        assigned_mentor_id=contact.assigned_mentor_id,
        assigned_mentor_name=None,
        branch_name=branch_name,
        foundation_class_status=contact.foundation_class_status,
        foundation_class_start_date=contact.foundation_class_start_date,
        foundation_class_completion_date=contact.foundation_class_completion_date,
        baptism_status=contact.baptism_status,
        cell_group=contact.cell_group,
        service_unit_id=contact.service_unit_id,
        service_unit_name=service_unit_name,
        service_unit_leader_name=service_unit_leader_name,
        service_unit_joined_at=contact.service_unit_joined_at,
        unit_active=contact.unit_active,
        second_visit_date=contact.second_visit_date,
        third_visit_date=contact.third_visit_date,
        last_attendance_date=contact.last_attendance_date,
        notes=contact.notes,
        consent_given=contact.consent_given,
        opt_out=contact.opt_out,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )
