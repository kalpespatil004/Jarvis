from datetime import datetime
from zoneinfo import ZoneInfo

from services.time_date.temporal_reasoner import TEMPORAL_REASONER


BASE = datetime(2026, 5, 15, 9, 30, tzinfo=ZoneInfo("America/New_York"))


def test_resolves_relative_expressions_with_timezone():
    tomorrow = TEMPORAL_REASONER.resolve("tomorrow", now=BASE, tz_name="America/New_York")
    day_after = TEMPORAL_REASONER.resolve("day after tomorrow", now=BASE, tz_name="America/New_York")
    next_monday = TEMPORAL_REASONER.resolve("next Monday", now=BASE, tz_name="America/New_York")

    assert tomorrow.iso_date == "2026-05-16"
    assert day_after.iso_date == "2026-05-17"
    assert next_monday.iso_date == "2026-05-18"
    assert next_monday.timezone == "America/New_York"


def test_resolves_partial_followup_next_week():
    resolution = TEMPORAL_REASONER.resolve_followup(
        "what about next week?",
        last_intent="get_date",
        last_date_ref="tomorrow",
        now=BASE,
        tz_name="America/New_York",
    )

    assert resolution is not None
    assert resolution.kind == "date_range"
    assert resolution.iso_date == "2026-05-18"
    assert resolution.end_iso_date == "2026-05-24"
    assert resolution.is_followup is True


def test_locale_safe_explicit_rendering():
    resolution = TEMPORAL_REASONER.resolve("next Monday", now=BASE, tz_name="America/New_York")

    assert TEMPORAL_REASONER.format_date(resolution) == "Monday, May 18, 2026"
