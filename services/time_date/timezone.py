"""
timezone.py
------------
Timezone conversion utilities
"""

from datetime import datetime
import pytz


def convert_timezone(
    time_str: str,
    from_timezone: str,
    to_timezone: str,
    format: str = "%Y-%m-%d %H:%M:%S"
) -> dict:
    """
    Convert time from one timezone to another.

    Args:
        time_str (str): Time string
        from_timezone (str): Source timezone (e.g. "Asia/Kolkata")
        to_timezone (str): Target timezone (e.g. "UTC")
        format (str): Datetime format

    Returns:
        dict: Converted time or error
    """

    try:
        source_tz = pytz.timezone(from_timezone)
        target_tz = pytz.timezone(to_timezone)

        naive_dt = datetime.strptime(time_str, format)
        source_dt = source_tz.localize(naive_dt)
        target_dt = source_dt.astimezone(target_tz)

        return {
            "success": True,
            "from_timezone": from_timezone,
            "to_timezone": to_timezone,
            "original_time": time_str,
            "converted_time": target_dt.strftime(format)
        }

    except pytz.UnknownTimeZoneError:
        return {
            "success": False,
            "error": "Invalid timezone name"
        }

    except ValueError:
        return {
            "success": False,
            "error": "Invalid time format"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
