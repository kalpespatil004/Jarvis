"""Time and date related services."""

from __future__ import annotations

import datetime as _dt

from brain.response_picker import get_response


def get_current_time_response() -> str:
    now = _dt.datetime.now().strftime("%I:%M %p")
    return get_response("get_time", now)


def get_current_date_response() -> str:
    today = _dt.datetime.now().strftime("%A, %d %B %Y")
    return get_response("get_date", today)
