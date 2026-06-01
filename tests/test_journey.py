from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.services.contact import ContactService
from app.models.contact import Contact
from app.models.church import Church, Branch
from app.models.follow_up import FollowUpTask, CommunicationLog
from app.models.service_unit import ServiceUnit
from app.models.user import User, Role


class TestContactJourney:
    @staticmethod
    async def _seed_full_journey(session):
        suffix = str(uuid4())[:8]
        church = Church(name=f"Church-{suffix}")
        session.add(church)
        await session.flush()

        branch = Branch(church_id=church.id, name=f"Branch-{suffix}")
        session.add(branch)
        await session.flush()

        role = Role(name=f"Role-{suffix}", description="Test role")
        session.add(role)
        await session.flush()

        user = User(church_id=church.id, branch_id=branch.id, role_id=role.id,
                    name=f"Pastor-{suffix}", email=f"{suffix}@test.com",
                    phone=f"+{suffix[:4]}", active=True)
        session.add(user)
        await session.flush()

        unit = ServiceUnit(church_id=church.id, branch_id=branch.id,
                          name=f"Unit-{suffix}", leader_id=user.id)
        session.add(unit)
        await session.flush()

        tz = timezone.utc
        contact = Contact(
            church_id=church.id, branch_id=branch.id,
            first_name="Jane", last_name="Smith",
            phone=f"+{suffix[:6]}", email=f"jane_{suffix}@test.com",
            category="first_timer", source="service", status="attending",
            assigned_worker_id=user.id, service_unit_id=unit.id,
            second_visit_date=datetime(2026, 5, 8, tzinfo=tz),
            third_visit_date=datetime(2026, 5, 22, tzinfo=tz),
            foundation_class_status="completed",
            foundation_class_start_date=datetime(2026, 5, 15, tzinfo=tz),
            foundation_class_completion_date=datetime(2026, 5, 27, tzinfo=tz),
            cell_group="Hope Cell", consent_given=True,
        )
        contact.created_at = datetime(2026, 5, 1, tzinfo=tz)
        session.add(contact)
        await session.flush()

        task = FollowUpTask(
            contact_id=contact.id, assigned_to=user.id, task_type="call",
            due_date=datetime(2026, 5, 2, tzinfo=tz), status="completed",
            priority="high", notes="Called to follow up.",
            completed_at=datetime(2026, 5, 2, tzinfo=tz),
        )
        task.created_at = datetime(2026, 5, 2, tzinfo=tz)
        session.add(task)
        await session.flush()

        log = CommunicationLog(
            contact_id=contact.id, channel="call", status="sent",
            message="Followed up with Jane.", outcome="positive",
            sent_by=user.id,
        )
        log.created_at = datetime(2026, 5, 2, tzinfo=tz)
        log.sent_at = datetime(2026, 5, 2, tzinfo=tz)
        session.add(log)
        await session.flush()

        await session.commit()
        return church.id, contact.id

    async def test_returns_contact_info(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        assert result is not None
        assert result.contact.first_name == "Jane"
        assert result.contact.last_name == "Smith"
        assert result.contact.status == "attending"
        assert result.contact.assigned_worker_name is not None
        assert "Pastor" in result.contact.assigned_worker_name

    async def test_current_stage_and_status(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        assert result.current_stage == "attending"
        assert result.foundation_class_status == "completed"
        assert result.service_unit_status is not None

    async def test_first_visit_date(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        assert result.first_visit_date is not None
        assert result.first_visit_date.year == 2026
        assert result.first_visit_date.month == 5
        assert result.first_visit_date.day == 1

    async def test_follow_up_history(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        assert len(result.follow_up_history) == 1
        fu = result.follow_up_history[0]
        assert fu.type == "follow_up"
        assert "Call" in fu.title
        assert fu.meta.get("task_type") == "call"
        assert fu.meta.get("priority") == "high"
        assert fu.meta.get("status") == "completed"

    async def test_communication_history(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        assert len(result.communication_history) == 1
        comm = result.communication_history[0]
        assert comm.type == "communication"
        assert comm.meta.get("channel") == "call"
        assert comm.meta.get("outcome") == "positive"

    async def test_timeline_is_chronological(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        assert len(result.timeline) >= 6
        dates = [e.date for e in result.timeline]
        assert dates == sorted(dates)

    async def test_timeline_has_registration_event(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        reg_events = [e for e in result.timeline if e.type == "registration"]
        assert len(reg_events) >= 1
        first = reg_events[0]
        assert first.title == "First Visit / Registration"
        assert first.meta.get("category") == "first_timer"

    async def test_timeline_has_return_visits(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        visit_events = [e for e in result.timeline
                       if "visit" in e.title.lower() or "Visit" in e.title]
        assert len(visit_events) >= 2

    async def test_timeline_has_foundation_class(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        fc = [e for e in result.timeline if e.type == "foundation_class"]
        assert len(fc) == 1
        assert "Completed" in fc[0].title
        assert fc[0].meta.get("completed") == "true"

    async def test_timeline_has_service_unit(self, session):
        church_id, contact_id = await self._seed_full_journey(session)
        svc = ContactService(session)
        result = await svc.get_contact_journey(contact_id, church_id)

        su = [e for e in result.timeline if e.type == "service_unit"]
        assert len(su) == 1

    async def test_contact_not_found_returns_none(self, session):
        svc = ContactService(session)
        result = await svc.get_contact_journey(99999, 1)
        assert result is None

    async def test_no_follow_ups_no_logs(self, session):
        suffix = str(uuid4())[:8]
        church = Church(name=f"Minimal-{suffix}")
        session.add(church)
        await session.flush()
        branch = Branch(church_id=church.id, name=f"Minimal-{suffix}")
        session.add(branch)
        await session.flush()
        contact = Contact(
            church_id=church.id, branch_id=branch.id,
            first_name="Min", last_name="Contact",
            phone=f"+{suffix[:6]}", category="first_timer", status="new",
            consent_given=True,
        )
        contact.created_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
        session.add(contact)
        await session.flush()
        await session.commit()

        svc = ContactService(session)
        result = await svc.get_contact_journey(contact.id, church.id)

        assert result is not None
        assert len(result.follow_up_history) == 0
        assert len(result.communication_history) == 0
        assert len(result.timeline) == 1
        assert result.timeline[0].type == "registration"
