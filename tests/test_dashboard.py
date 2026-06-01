import math
import pytest
from datetime import datetime, timezone

from app.services.dashboard import DashboardService
from app.models.contact import Contact
from app.models.church import Church, Branch


class TestSafeRate:
    @pytest.mark.parametrize(
        "numerator,denominator,expected",
        [
            (0, 100, 0.0),
            (50, 100, 50.0),
            (1, 3, 100 / 3),
            (100, 100, 100.0),
        ],
    )
    def test_normal_calculations(self, numerator, denominator, expected):
        result = DashboardService._safe_rate(numerator, denominator)
        assert math.isclose(result, expected, rel_tol=1e-12)

    def test_zero_denominator_returns_zero(self):
        assert DashboardService._safe_rate(50, 0) == 0.0
        assert DashboardService._safe_rate(0, 0) == 0.0

    def test_negative_denominator_returns_zero(self):
        assert DashboardService._safe_rate(50, -1) == 0.0

    def test_negative_numerator_returns_zero(self):
        assert DashboardService._safe_rate(-1, 100) == 0.0

    def test_none_values_returns_zero(self):
        assert DashboardService._safe_rate(None, 100) == 0.0
        assert DashboardService._safe_rate(50, None) == 0.0
        assert DashboardService._safe_rate(None, None) == 0.0

    def test_non_numeric_values_returns_zero(self):
        assert DashboardService._safe_rate("abc", 100) == 0.0
        assert DashboardService._safe_rate(50, "xyz") == 0.0

    def test_float_nan_returns_zero(self):
        assert DashboardService._safe_rate(float("nan"), 100) == 0.0
        assert DashboardService._safe_rate(50, float("nan")) == 0.0

    def test_float_inf_returns_zero(self):
        assert DashboardService._safe_rate(float("inf"), 100) == 0.0
        assert DashboardService._safe_rate(float("-inf"), 100) == 0.0
        assert DashboardService._safe_rate(50, float("inf")) == 0.0

    def test_small_fractions(self):
        assert math.isclose(DashboardService._safe_rate(1, 1000), 0.1)

    def test_result_nan_returns_zero(self):
        assert DashboardService._safe_rate(0, 0) == 0.0


class TestReturnStats:
    @staticmethod
    async def _seed_church(session, name="Test Church"):
        church = Church(name=name)
        session.add(church)
        await session.flush()
        branch = Branch(church_id=church.id, name=f"{name} Branch")
        session.add(branch)
        await session.flush()
        return church.id, branch.id

    @staticmethod
    async def _create_first_timer(session, church_id, branch_id, **kwargs):
        defaults = {
            "church_id": church_id,
            "branch_id": branch_id,
            "first_name": "Test",
            "last_name": "Contact",
            "phone": f"555-{datetime.now(timezone.utc).microsecond:06d}",
            "category": "first_timer",
            "status": "new",
        }
        defaults.update(kwargs)
        contact = Contact(**defaults)
        session.add(contact)
        await session.flush()
        return contact

    async def test_no_first_timers(self, session):
        church_id, _ = await self._seed_church(session)
        await session.commit()

        svc = DashboardService(session)
        total, return_rate, retention_rate = await svc._return_stats(church_id)

        assert total == 0
        assert return_rate == 0.0
        assert retention_rate == 0.0

    async def test_no_return_visitors(self, session):
        church_id, branch_id = await self._seed_church(session)
        await self._create_first_timer(session, church_id, branch_id)
        await self._create_first_timer(session, church_id, branch_id)
        await session.commit()

        svc = DashboardService(session)
        total, return_rate, retention_rate = await svc._return_stats(church_id)

        assert total == 2
        assert return_rate == 0.0
        assert retention_rate == 0.0

    async def test_no_retained_visitors(self, session):
        church_id, branch_id = await self._seed_church(session)
        await self._create_first_timer(
            session, church_id, branch_id,
            second_visit_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            status="new",
        )
        await session.commit()

        svc = DashboardService(session)
        total, return_rate, retention_rate = await svc._return_stats(church_id)

        assert total == 1
        assert return_rate == 100.0
        assert retention_rate == 0.0

    async def test_normal_calculations(self, session):
        church_id, branch_id = await self._seed_church(session)
        tz = timezone.utc
        for i in range(10):
            second_visit = datetime(2025, 1, 15, tzinfo=tz) if i < 6 else None
            status = "attending" if i < 4 else "new"
            await self._create_first_timer(
                session, church_id, branch_id,
                phone=f"555-{i:04d}",
                second_visit_date=second_visit,
                status=status,
            )
        await session.commit()

        svc = DashboardService(session)
        total, return_rate, retention_rate = await svc._return_stats(church_id)

        assert total == 10
        assert return_rate == 60.0
        assert retention_rate == 40.0

    async def test_all_returned_and_retained(self, session):
        church_id, branch_id = await self._seed_church(session)
        tz = timezone.utc
        for i in range(5):
            await self._create_first_timer(
                session, church_id, branch_id,
                phone=f"555-{i:04d}",
                second_visit_date=datetime(2025, 1, 15, tzinfo=tz),
                status="completed",
            )
        await session.commit()

        svc = DashboardService(session)
        total, return_rate, retention_rate = await svc._return_stats(church_id)

        assert total == 5
        assert return_rate == 100.0
        assert retention_rate == 100.0

    async def test_church_isolation(self, session):
        church_a_id, branch_a_id = await self._seed_church(session, name="Church A")
        await self._create_first_timer(session, church_a_id, branch_a_id, status="attending")
        church_b_id, _ = await self._seed_church(session, name="Church B")
        await session.commit()

        svc = DashboardService(session)
        total_a, ret_a, _ = await svc._return_stats(church_a_id)
        total_b, ret_b, _ = await svc._return_stats(church_b_id)

        assert total_a == 1
        assert ret_a == 0.0
        assert total_b == 0
        assert ret_b == 0.0

    async def test_soft_deleted_contacts_excluded(self, session):
        tz = timezone.utc
        church_id, branch_id = await self._seed_church(session)
        await self._create_first_timer(
            session, church_id, branch_id,
            second_visit_date=datetime(2025, 1, 15, tzinfo=tz),
            status="attending",
        )
        await self._create_first_timer(
            session, church_id, branch_id,
            phone="555-deleted",
            second_visit_date=datetime(2025, 1, 15, tzinfo=tz),
            status="attending",
            deleted_at=datetime(2025, 3, 1, tzinfo=tz),
        )
        await session.commit()

        svc = DashboardService(session)
        total, return_rate, retention_rate = await svc._return_stats(church_id)

        assert total == 1
        assert return_rate == 100.0
        assert retention_rate == 100.0
