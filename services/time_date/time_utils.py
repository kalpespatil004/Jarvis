"""
services/time_date/time_utils.py
---------------------------------
Current time and date utilities.
"""

import datetime


def current_time() -> str:
    return datetime.datetime.now().strftime("%I:%M %p")


def current_date() -> str:
    return datetime.datetime.now().strftime("%A, %d %B %Y")


def current_datetime() -> str:
    return datetime.datetime.now().strftime("%A, %d %B %Y – %I:%M %p")


def day_of_week() -> str:
    return datetime.datetime.now().strftime("%A")


def week_number() -> str:
    return str(datetime.datetime.now().isocalendar()[1])
