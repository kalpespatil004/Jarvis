"""
time_utils.py
--------------
Utility functions related to current date and time
"""

from datetime import datetime


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


def current_date() -> str:
    """
    Get current date only.

    Returns:
        str
    """
    return datetime.now().strftime("%Y-%m-%d")


def current_time_only() -> str:
    """
    Get current time only.

    Returns:
        str
    """
    return datetime.now().strftime("%H:%M:%S")
