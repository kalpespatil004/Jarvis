"""
services/time_date/timezone.py
--------------------------------
Timezone conversion utilities.
"""

import datetime

try:
    import pytz
    _PYTZ = True
except ImportError:
    _PYTZ = False


def convert_timezone(time_str: str, from_tz: str, to_tz: str) -> str:
    if not _PYTZ:
        return "pytz not installed. Run: pip install pytz"

    try:
        from_zone = pytz.timezone(from_tz)
        to_zone   = pytz.timezone(to_tz)

        # Parse time string
        naive_time = datetime.datetime.strptime(time_str.strip(), "%H:%M")
        today = datetime.datetime.now().date()
        aware_time = datetime.datetime(today.year, today.month, today.day,
                                        naive_time.hour, naive_time.minute)
        aware_time = from_zone.localize(aware_time)
        converted  = aware_time.astimezone(to_zone)

        return (
            f"🕐 {time_str} {from_tz} = "
            f"{converted.strftime('%I:%M %p')} {to_tz}"
        )
    except pytz.UnknownTimeZoneError as e:
        return f"Unknown timezone: {e}"
    except Exception as e:
        return f"Timezone conversion error: {e}"
