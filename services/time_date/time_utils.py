"""
time_utils.py
--------------
Utility functions related to current date and time
"""

from __future__ import annotations

from datetime import datetime, timedelta


def current_time(format: str = "%Y-%m-%d %H:%M:%S") -> dict:
    """
    Get current system time.

    Args:
        format (str): Datetime format string

    Returns:
        dict: Current time data
    """

    try:
        now = datetime.now()
        return {
            "success": True,
            "timestamp": now.timestamp(),
            "formatted": now.strftime(format),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def date_for_ref(date_ref: str = "today") -> datetime:
    """Return datetime for a relative day reference (today/tomorrow/yesterday)."""
    base = datetime.now()
    ref = (date_ref or "today").strip().lower()
    if ref == "tomorrow":
        return base + timedelta(days=1)
    if ref == "yesterday":
        return base - timedelta(days=1)
    return base


def current_date(date_ref: str = "today") -> str:
    """Get current date (or relative date) in YYYY-MM-DD format."""
    return date_for_ref(date_ref).strftime("%Y-%m-%d")


def current_weekday(date_ref: str = "today") -> str:
    """Get weekday name for a relative date reference."""
    return date_for_ref(date_ref).strftime("%A")


def current_time_only() -> str:
    """
    Get current time only.

    Returns:
        str
    """
    return datetime.now().strftime("%H:%M:%S")
