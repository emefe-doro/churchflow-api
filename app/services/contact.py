import csv
import io
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact
from app.models.follow_up import FollowUpTask, CommunicationLog
from app.models.service_unit import ServiceUnit
from app.schemas.contact import (
    ContactCreate,
    ContactFilter,
    ContactJourneyResponse,
    ContactResponse,
    ContactUpdate,
    CSVRowResult,
    CSVUploadResponse,
    DuplicateCheckResponse,
    JourneyEvent,
)
class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_contact(self, data: ContactCreate) -> Contact:
        now = datetime.now(timezone.utc)
        contact = Contact(
            church_id=data.church_id,
            branch_id=data.branch_id,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            phone=data.phone.strip(),
            email=data.email.strip() if data.email else None,
            gender=data.gender,
            age_group=data.age_group,
            address=data.address,
            category=data.category,
            source=data.source,
            status=data.status or "new",
            assigned_worker_id=data.assigned_worker_id,
            foundation_class_status=data.foundation_class_status,
            foundation_class_start_date=data.foundation_class_start_date,
            foundation_class_completion_date=data.foundation_class_completion_date,
            baptism_status=data.baptism_status,
            cell_group=data.cell_group.strip() if data.cell_group else None,
            assigned_mentor_id=data.assigned_mentor_id,
            service_unit_id=data.service_unit_id,
            service_unit_joined_at=data.service_unit_joined_at or now if data.service_unit_id else None,
            unit_active=data.unit_active if data.unit_active is not None else True,
            second_visit_date=data.second_visit_date,
            third_visit_date=data.third_visit_date,
            last_attendance_date=data.last_attendance_date,
            notes=data.notes,
            consent_given=data.consent_given,
        )
        self.db.add(contact)
        await self.db.flush()
        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.assigned_worker),
                joinedload(Contact.assigned_mentor),
                joinedload(Contact.branch),
                joinedload(Contact.service_unit).joinedload(ServiceUnit.leader),
            )
            .where(Contact.id == contact.id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one()

    async def get_contact(self, contact_id: int, church_id: int | None = None) -> Contact | None:
        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.assigned_worker),
                joinedload(Contact.assigned_mentor),
                joinedload(Contact.branch),
                joinedload(Contact.service_unit),
            )
            .where(Contact.id == contact_id, Contact.deleted_at.is_(None))
        )
        if church_id is not None:
            stmt = stmt.where(Contact.church_id == church_id)
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_contacts(
        self, church_id: int, filters: ContactFilter | None = None
    ) -> tuple[list[Contact], int]:
        if filters is None:
            filters = ContactFilter()

        conditions = [Contact.church_id == church_id, Contact.deleted_at.is_(None)]

        if filters.category:
            conditions.append(Contact.category == filters.category)
        if filters.status:
            conditions.append(Contact.status == filters.status)
        if filters.source:
            conditions.append(Contact.source == filters.source)
        if filters.assigned_worker_id is not None:
            conditions.append(Contact.assigned_worker_id == filters.assigned_worker_id)
        if filters.branch_id is not None:
            conditions.append(Contact.branch_id == filters.branch_id)
        if filters.foundation_class_status:
            conditions.append(Contact.foundation_class_status == filters.foundation_class_status)
        if filters.date_from:
            conditions.append(Contact.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(Contact.created_at <= filters.date_to)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Contact.first_name.ilike(search_term),
                    Contact.last_name.ilike(search_term),
                    Contact.phone.ilike(search_term),
                    Contact.email.ilike(search_term),
                )
            )

        where_clause = and_(*conditions)

        count_stmt = select(func.count(Contact.id)).where(where_clause)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (filters.page - 1) * filters.page_size
        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.assigned_worker),
                joinedload(Contact.assigned_mentor),
                joinedload(Contact.branch),
                joinedload(Contact.service_unit).joinedload(ServiceUnit.leader),
            )
            .where(where_clause)
            .order_by(Contact.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(stmt)
        contacts = list(result.unique().scalars().all())

        return contacts, total

    async def get_first_timers(
        self, church_id: int, filters: ContactFilter | None = None
    ) -> tuple[list[Contact], int]:
        if filters is None:
            filters = ContactFilter()
        filters.category = "first_timer"
        return await self.get_contacts(church_id, filters)

    async def get_new_converts(
        self, church_id: int, filters: ContactFilter | None = None
    ) -> tuple[list[Contact], int]:
        if filters is None:
            filters = ContactFilter()
        filters.category = "new_convert"
        return await self.get_contacts(church_id, filters)

    async def get_outreach_converts(
        self, church_id: int, filters: ContactFilter | None = None
    ) -> tuple[list[Contact], int]:
        if filters is None:
            filters = ContactFilter()
        filters.category = "outreach_convert"
        return await self.get_contacts(church_id, filters)

    async def update_contact(self, contact_id: int, data: ContactUpdate, church_id: int) -> Contact | None:
        contact = await self.get_contact(contact_id, church_id)
        if contact is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        previous_unit_id = contact.service_unit_id

        for key, value in update_data.items():
            if value is not None and hasattr(contact, key):
                setattr(contact, key, value.strip() if isinstance(value, str) else value)

        if contact.service_unit_id and contact.service_unit_id != previous_unit_id:
            if "service_unit_joined_at" not in update_data or update_data.get("service_unit_joined_at") is None:
                contact.service_unit_joined_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, church_id: int) -> bool:
        contact = await self.get_contact(contact_id, church_id)
        if contact is None:
            return False
        contact.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def check_duplicate_phone(
        self, church_id: int, phone: str, exclude_contact_id: int | None = None
    ) -> DuplicateCheckResponse:
        conditions = [
            Contact.church_id == church_id,
            Contact.phone == phone.strip(),
            Contact.deleted_at.is_(None),
        ]
        if exclude_contact_id is not None:
            conditions.append(Contact.id != exclude_contact_id)

        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.assigned_worker),
                joinedload(Contact.assigned_mentor),
                joinedload(Contact.branch),
                joinedload(Contact.service_unit),
            )
            .where(and_(*conditions))
        )
        result = await self.db.execute(stmt)
        existing = list(result.unique().scalars().all())

        return DuplicateCheckResponse(
            phone=phone,
            is_duplicate=len(existing) > 0,
            existing_contacts=[
                self._to_response(c) for c in existing
            ],
        )

    async def upload_csv(
        self, church_id: int, branch_id: int, file_content: bytes
    ) -> CSVUploadResponse:
        decoded = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        results: list[CSVRowResult] = []
        created = 0
        skipped = 0
        errors = 0

        required_fields = {"first_name", "last_name", "phone", "category"}
        header_lower = {h.lower() for h in (reader.fieldnames or [])}
        missing = required_fields - header_lower
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        for idx, row in enumerate(reader, start=2):
            row_lower = {k.lower().strip(): v.strip() if v else "" for k, v in row.items()}

            phone = row_lower.get("phone", "")
            first_name = row_lower.get("first_name", "")
            last_name = row_lower.get("last_name", "")
            category = row_lower.get("category", "").lower().replace(" ", "_")

            if not all([phone, first_name, last_name, category]):
                results.append(CSVRowResult(
                    row=idx, phone=phone, status="error",
                    message="Missing required fields (first_name, last_name, phone, category)",
                ))
                errors += 1
                continue

            if category not in ("first_timer", "new_convert", "outreach_convert", "member", "other"):
                results.append(CSVRowResult(
                    row=idx, phone=phone, status="error",
                    message=f"Invalid category: {category}",
                ))
                errors += 1
                continue

            dup_check = await self.check_duplicate_phone(church_id, phone)
            if dup_check.is_duplicate:
                results.append(CSVRowResult(
                    row=idx, phone=phone, status="skipped",
                    message=f"Duplicate phone: existing contact ID {dup_check.existing_contacts[0].id}",
                ))
                skipped += 1
                continue

            try:
                contact = Contact(
                    church_id=church_id,
                    branch_id=branch_id,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=row_lower.get("email") or None,
                    gender=row_lower.get("gender") or None,
                    age_group=row_lower.get("age_group") or None,
                    address=row_lower.get("address") or None,
                    category=category,
                    source=row_lower.get("source") or None,
                    notes=row_lower.get("notes") or None,
                    consent_given=row_lower.get("consent_given", "").lower() in ("true", "yes", "1"),
                )
                self.db.add(contact)
                await self.db.flush()
                results.append(CSVRowResult(
                    row=idx, phone=phone, status="created",
                    message="Contact created successfully",
                    contact_id=contact.id,
                ))
                created += 1
            except Exception as e:
                results.append(CSVRowResult(
                    row=idx, phone=phone, status="error",
                    message=str(e),
                ))
                errors += 1

        return CSVUploadResponse(
            total_rows=len(results),
            created=created,
            skipped=skipped,
            errors=errors,
            results=results,
        )

    def _to_response(self, contact: Contact) -> ContactResponse:
        worker_name = None
        if contact.assigned_worker:
            worker_name = contact.assigned_worker.name

        mentor_name = None
        if contact.assigned_mentor:
            mentor_name = contact.assigned_mentor.name

        branch_name = None
        if contact.branch:
            branch_name = contact.branch.name

        service_unit_name = None
        service_unit_leader_name = None
        if contact.service_unit:
            service_unit_name = contact.service_unit.name
            if contact.service_unit.leader:
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
            assigned_mentor_name=mentor_name,
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

    async def get_contact_journey(self, contact_id: int, church_id: int) -> ContactJourneyResponse | None:
        stmt = (
            select(Contact)
            .options(
                joinedload(Contact.assigned_worker),
                joinedload(Contact.assigned_mentor),
                joinedload(Contact.branch),
                joinedload(Contact.service_unit),
                joinedload(Contact.tasks).joinedload(FollowUpTask.assigned_user),
                joinedload(Contact.communication_logs).joinedload(CommunicationLog.sender),
            )
            .where(Contact.id == contact_id, Contact.church_id == church_id, Contact.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        contact = result.unique().scalar_one_or_none()
        if contact is None:
            return None

        follow_up_history: list[JourneyEvent] = []
        for task in contact.tasks or []:
            meta = {}
            if task.task_type:
                meta["task_type"] = task.task_type
            if task.priority:
                meta["priority"] = task.priority
            if task.assigned_user:
                meta["assigned_to"] = task.assigned_user.name
            if task.status:
                meta["status"] = task.status
            if task.notes:
                meta["notes"] = task.notes

            follow_up_history.append(JourneyEvent(
                id=f"task-{task.id}",
                type="follow_up",
                title=f"Follow-up: {task.task_type.replace('_', ' ').title()}",
                description=task.notes or f"{task.task_type.replace('_', ' ').title()} follow-up",
                date=task.created_at,
                icon=_task_type_icon(task.task_type),
                meta=meta,
            ))

        communication_history: list[JourneyEvent] = []
        for log in contact.communication_logs or []:
            meta = {}
            if log.channel:
                meta["channel"] = log.channel
            if log.outcome:
                meta["outcome"] = log.outcome
            if log.sender:
                meta["sent_by"] = log.sender.name
            if log.status:
                meta["status"] = log.status
            if log.message:
                meta["message"] = log.message

            communication_history.append(JourneyEvent(
                id=f"comm-{log.id}",
                type="communication",
                title=f"Communication: {log.channel.replace('_', ' ').title()}",
                description=log.message or f"{log.channel.replace('_', ' ').title()} communication",
                date=log.sent_at or log.created_at,
                icon=_comm_channel_icon(log.channel),
                meta=meta,
            ))

        service_unit_status = None
        if contact.service_unit:
            service_unit_status = contact.service_unit.name
        elif contact.cell_group:
            service_unit_status = contact.cell_group

        timeline: list[JourneyEvent] = []

        timeline.append(JourneyEvent(
            id=f"registration-{contact.id}",
            type="registration",
            title="First Visit / Registration",
            description=f"Contact registered as {contact.category.replace('_', ' ').title()}",
            date=contact.created_at,
            icon="UserPlus",
            meta={"category": contact.category},
        ))

        if contact.second_visit_date:
            timeline.append(JourneyEvent(
                id=f"second-visit-{contact.id}",
                type="registration",
                title="Second Visit",
                description=f"Returned for a second visit on {contact.second_visit_date.strftime('%b %d, %Y')}",
                date=contact.second_visit_date,
                icon="UserCheck",
            ))

        if contact.third_visit_date:
            timeline.append(JourneyEvent(
                id=f"third-visit-{contact.id}",
                type="registration",
                title="Third Visit",
                description=f"Returned for a third visit on {contact.third_visit_date.strftime('%b %d, %Y')}",
                date=contact.third_visit_date,
                icon="UserCheck",
            ))

        if contact.last_attendance_date and contact.last_attendance_date != contact.third_visit_date and contact.last_attendance_date != contact.second_visit_date:
            timeline.append(JourneyEvent(
                id=f"last-attendance-{contact.id}",
                type="registration",
                title="Last Attendance",
                description=f"Most recent attendance recorded on {contact.last_attendance_date.strftime('%b %d, %Y')}",
                date=contact.last_attendance_date,
                icon="CalendarCheck",
            ))

        if contact.foundation_class_status:
            meta = {}
            if contact.foundation_class_status == "completed":
                meta["completed"] = "true"
            event_date = contact.foundation_class_completion_date or contact.foundation_class_start_date or contact.updated_at
            description = f"Foundation class status is {contact.foundation_class_status.replace('_', ' ')}"
            if contact.foundation_class_start_date:
                meta["start_date"] = contact.foundation_class_start_date.isoformat()
                description += f" — Started {contact.foundation_class_start_date.strftime('%b %d, %Y')}"
            if contact.foundation_class_completion_date:
                meta["completion_date"] = contact.foundation_class_completion_date.isoformat()
                description += f" — Completed {contact.foundation_class_completion_date.strftime('%b %d, %Y')}"
            timeline.append(JourneyEvent(
                id=f"foundation-{contact.id}",
                type="foundation_class",
                title=f"Foundation Class: {contact.foundation_class_status.replace('_', ' ').title()}",
                description=description,
                date=event_date,
                icon="BookOpen",
                meta=meta,
            ))

        if contact.service_unit:
            timeline.append(JourneyEvent(
                id=f"service-unit-{contact.id}",
                type="service_unit",
                title=f"Service Unit: {contact.service_unit.name}",
                description=f"Assigned to {contact.service_unit.name} service unit",
                date=contact.updated_at,
                icon="Building2",
                meta={"unit_name": contact.service_unit.name},
            ))

        for event in follow_up_history:
            timeline.append(event)

        for event in communication_history:
            timeline.append(event)

        timeline.sort(key=lambda e: e.date)

        return ContactJourneyResponse(
            contact=self._to_response(contact),
            current_stage=contact.status or "new",
            first_visit_date=contact.created_at,
            assigned_worker_name=contact.assigned_worker.name if contact.assigned_worker else None,
            foundation_class_status=contact.foundation_class_status,
            service_unit_status=service_unit_status,
            follow_up_history=follow_up_history,
            communication_history=communication_history,
            timeline=timeline,
        )


def _task_type_icon(task_type: str) -> str:
    icons = {
        "call": "Phone",
        "message": "MessageSquare",
        "visit": "MapPin",
        "invite": "Mail",
        "other": "MoreHorizontal",
    }
    return icons.get(task_type, "ClipboardList")


def _comm_channel_icon(channel: str) -> str:
    icons = {
        "whatsapp": "MessageCircle",
        "sms": "MessageSquare",
        "call": "Phone",
        "email": "Mail",
        "visit": "MapPin",
        "manual": "ClipboardList",
    }
    return icons.get(channel, "MessageSquare")
