"""Timezone-aware temporal expression resolution for Jarvis.

The reasoner keeps date parsing deterministic and locale-safe for simple
calendar utterances such as "today", "tomorrow", "next Monday", and
follow-up fragments like "tomorrow's?".
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_WEEKDAY_LOOKUP = {name.lower(): idx for idx, name in enumerate(_WEEKDAY_NAMES)}
_WEEKDAY_PATTERN = "|".join(name.lower() for name in _WEEKDAY_NAMES)


@dataclass(frozen=True)
class TemporalResolution:
    """Resolved temporal anchor suitable for intent slots and responses."""

    expression: str
    label: str
    start: date
    end: date | None
    timezone: str
    kind: str = "date"
    is_followup: bool = False

    @property
    def iso_date(self) -> str:
        return self.start.isoformat()

    @property
    def end_iso_date(self) -> str | None:
        return self.end.isoformat() if self.end else None

    def as_slots(self) -> dict[str, Any]:
        slots: dict[str, Any] = {
            "date_ref": self.expression,
            "resolved_date": self.iso_date,
            "resolved_date_label": self.label,
            "resolved_timezone": self.timezone,
            "temporal_kind": self.kind,
            "temporal_followup": self.is_followup,
        }
        if self.end is not None:
            slots["resolved_end_date"] = self.end_iso_date
        return slots


class TemporalReasoner:
    """Resolve simple date references relative to a timezone-aware clock."""

    def resolve(
        self,
        utterance: str | None = None,
        *,
        date_ref: str | None = None,
        now: datetime | None = None,
        tz_name: str | None = None,
        last_date_ref: str | None = None,
    ) -> TemporalResolution:
        tz = self._coerce_timezone(tz_name)
        current = self._aware_now(now, tz)
        raw_expression = (date_ref or utterance or "today").strip()
        normalized = self._normalize(raw_expression)
        expression, kind, is_followup = self._extract_expression(normalized, last_date_ref)

        today = current.date()
        if expression == "today":
            return self._single(expression, "today", today, tz, is_followup)
        if expression == "yesterday":
            return self._single(expression, "yesterday", today - timedelta(days=1), tz, is_followup)
        if expression == "tomorrow":
            return self._single(expression, "tomorrow", today + timedelta(days=1), tz, is_followup)
        if expression == "day after tomorrow":
            return self._single(expression, "the day after tomorrow", today + timedelta(days=2), tz, is_followup)
        if expression == "next week" or kind == "week":
            days_until_monday = (7 - today.weekday()) % 7 or 7
            start = today + timedelta(days=days_until_monday)
            end = start + timedelta(days=6)
            return TemporalResolution(
                expression="next week",
                label="next week",
                start=start,
                end=end,
                timezone=self._timezone_name(tz),
                kind="date_range",
                is_followup=is_followup,
            )

        weekday_match = re.fullmatch(rf"next\s+({_WEEKDAY_PATTERN})", expression)
        if weekday_match:
            weekday = weekday_match.group(1)
            target_idx = _WEEKDAY_LOOKUP[weekday]
            days_ahead = (target_idx - today.weekday()) % 7 or 7
            return self._single(expression, f"next {_WEEKDAY_NAMES[target_idx]}", today + timedelta(days=days_ahead), tz, is_followup)

        # Unknown or unsupported temporal expression: keep behavior safe and anchor to today.
        return self._single("today", "today", today, tz, is_followup)

    def resolve_followup(
        self,
        utterance: str,
        *,
        last_intent: str | None = None,
        last_date_ref: str | None = None,
        now: datetime | None = None,
        tz_name: str | None = None,
    ) -> TemporalResolution | None:
        """Resolve elliptical temporal follow-ups after date/time turns."""

        if last_intent not in {"get_date", "get_time"} and not last_date_ref:
            return None
        normalized = self._normalize(utterance)
        if not self._looks_temporal(normalized):
            return None
        return self.resolve(utterance, now=now, tz_name=tz_name, last_date_ref=last_date_ref)

    def format_date(self, resolution: TemporalResolution) -> str:
        """Locale-safe explicit date rendering, e.g. Friday, May 15, 2026."""

        if resolution.end is not None:
            return f"{self._format_single_date(resolution.start)} through {self._format_single_date(resolution.end)}"
        return self._format_single_date(resolution.start)

    def format_time(self, now: datetime | None = None, *, tz_name: str | None = None, include_seconds: bool = True) -> str:
        tz = self._coerce_timezone(tz_name)
        current = self._aware_now(now, tz)
        if include_seconds:
            return f"{current.hour:02d}:{current.minute:02d}:{current.second:02d}"
        return f"{current.hour:02d}:{current.minute:02d}"

    def _extract_expression(self, normalized: str, last_date_ref: str | None) -> tuple[str, str, bool]:
        text = normalized.strip()
        is_followup = self._looks_like_partial_followup(text)

        if re.search(r"\b(day\s+after\s+tomorrow|overmorrow)\b", text):
            return "day after tomorrow", "date", is_followup
        if re.search(r"\b(tomorrow|tommorow|tomarow|tomarrows|tomorrows)\b", text):
            return "tomorrow", "date", is_followup
        if re.search(r"\b(yesterday|yestarday)\b", text):
            return "yesterday", "date", is_followup
        if re.search(r"\b(today|todays)\b", text):
            return "today", "date", is_followup
        if re.search(r"\bnext\s+week\b", text):
            return "next week", "week", is_followup
        weekday = re.search(rf"\bnext\s+({_WEEKDAY_PATTERN})\b", text)
        if weekday:
            return f"next {weekday.group(1)}", "date", is_followup
        if text in {"what about", "and", "then", "that", "same"} and last_date_ref:
            return self._normalize(last_date_ref), "date", True
        if last_date_ref and self._looks_like_partial_followup(text):
            return self._normalize(last_date_ref), "date", True
        return "today", "date", is_followup

    def _looks_temporal(self, normalized: str) -> bool:
        return bool(
            re.search(
                rf"\b(today|todays|tomorrow|tommorow|tomarow|tomarrows|tomorrows|yesterday|yestarday|"
                rf"day\s+after\s+tomorrow|overmorrow|next\s+week|next\s+(?:{_WEEKDAY_PATTERN}))\b",
                normalized,
            )
        )

    @staticmethod
    def _looks_like_partial_followup(normalized: str) -> bool:
        return bool(
            re.fullmatch(
                rf"(?:and\s+)?(?:what\s+about\s+)?"
                rf"(?:todays|tomorrows|yesterdays|today|tomorrow|yesterday|"
                rf"day\s+after\s+tomorrow|next\s+week|next\s+(?:{_WEEKDAY_PATTERN}))",
                normalized,
            )
            and (normalized.startswith("and ") or normalized.startswith("what about ") or normalized.endswith("s"))
        )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.lower().strip()
        normalized = re.sub(r"['’]s\b", "s", normalized)
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _single(self, expression: str, label: str, value: date, tz: timezone | ZoneInfo, is_followup: bool) -> TemporalResolution:
        return TemporalResolution(
            expression=expression,
            label=label,
            start=value,
            end=None,
            timezone=self._timezone_name(tz),
            kind="date",
            is_followup=is_followup,
        )

    def _format_single_date(self, value: date) -> str:
        weekday = _WEEKDAY_NAMES[value.weekday()]
        month = _MONTH_NAMES[value.month - 1]
        return f"{weekday}, {month} {value.day}, {value.year}"

    def _aware_now(self, now: datetime | None, tz: timezone | ZoneInfo) -> datetime:
        if now is None:
            return datetime.now(tz)
        if now.tzinfo is None:
            return now.replace(tzinfo=tz)
        return now.astimezone(tz)

    def _coerce_timezone(self, tz_name: str | None) -> timezone | ZoneInfo:
        name = (tz_name or os.environ.get("TZ") or "").strip()
        if name:
            try:
                return ZoneInfo(name)
            except ZoneInfoNotFoundError:
                pass
        if time.daylight and time.localtime().tm_isdst > 0:
            local_name = time.tzname[1]
        else:
            local_name = time.tzname[0]
        try:
            if local_name:
                return ZoneInfo(local_name)
        except ZoneInfoNotFoundError:
            pass
        return timezone.utc

    @staticmethod
    def _timezone_name(tz: timezone | ZoneInfo) -> str:
        key = getattr(tz, "key", None)
        if key:
            return str(key)
        name = tz.tzname(datetime.combine(date.today(), dt_time()))
        return name or "UTC"


TEMPORAL_REASONER = TemporalReasoner()
