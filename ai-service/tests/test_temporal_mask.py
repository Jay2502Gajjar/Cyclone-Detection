"""Invariant I1 — the temporal mask, enforced at the AI service boundary.

Spring Boot filters history before sending it. This is the second, independent filter.
The redundancy is deliberate: a leak would not present as a crash, it would present as a
suspiciously accurate hindcast, and that is the hardest kind of bug to notice while
demonstrating the product.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.forecast import HistoryPoint, InferFullRequest

AS_OF = datetime(2019, 5, 2, 6, 0, tzinfo=timezone.utc)


def point(offset_hours: float, vmax: float = 120.0) -> HistoryPoint:
    return HistoryPoint(
        t=AS_OF + timedelta(hours=offset_hours), lat=17.0, lon=85.0, vmaxKt=vmax
    )


def request_with(points: list[HistoryPoint]) -> InferFullRequest:
    return InferFullRequest(sid="2019114N06084", asOf=AS_OF, history=points)


class TestTemporalMask:
    def test_accepts_history_entirely_at_or_before_as_of(self):
        request = request_with([point(-24), point(-12), point(-6), point(0)])
        assert len(request.history) == 4

    def test_accepts_the_boundary_point_at_exactly_as_of(self):
        request = request_with([point(-6), point(0)])
        assert request.latest().t == AS_OF

    def test_rejects_a_single_future_observation(self):
        with pytest.raises(ValidationError, match="temporal mask violation"):
            request_with([point(-6), point(0), point(3)])

    def test_rejects_a_future_observation_even_when_it_is_the_only_one(self):
        with pytest.raises(ValidationError, match="temporal mask violation"):
            request_with([point(6)])

    def test_error_names_the_earliest_offender(self):
        with pytest.raises(ValidationError) as exc:
            request_with([point(0), point(48), point(12)])
        assert "2019-05-02T18:00" in str(exc.value)

    def test_rejects_rather_than_silently_dropping(self):
        # Quietly discarding the offending points would hide the caller's bug, which is
        # the failure this guard exists to expose.
        with pytest.raises(ValidationError):
            request_with([point(-3), point(3)])

    def test_requires_at_least_one_observation(self):
        with pytest.raises(ValidationError):
            request_with([])

    def test_latest_returns_the_most_recent_observable_point(self):
        request = request_with([point(-24), point(0), point(-6)])
        assert request.latest().t == AS_OF


class TestContractShape:
    def test_request_has_no_field_that_could_carry_the_future(self):
        fields = set(InferFullRequest.model_fields)
        assert fields == {"sid", "asOf", "history", "frameRef", "options"}

    def test_response_has_no_verification_field(self):
        # Invariant I2: ground truth must not be able to round-trip through inference.
        from app.schemas.forecast import InferFullResponse

        fields = set(InferFullResponse.model_fields)
        assert "verification" not in fields
        assert "degraded" not in fields
        assert "servedFrom" not in fields
