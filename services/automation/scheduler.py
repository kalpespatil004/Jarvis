"""
scheduler.py
-------------
Simple time-based task scheduler
"""

import time
from typing import Callable, Any


def schedule_task(
    delay_seconds: int,
    task: Callable[[], Any]
) -> dict:
    """
    Execute a task after a delay.

    Args:
        delay_seconds (int): Delay in seconds
        task (callable): Function to execute

    Returns:
        dict: Execution result
    """

    if not isinstance(delay_seconds, int) or delay_seconds < 0:
        return {
            "success": False,
            "error": "Delay must be a non-negative integer"
        }

    if not callable(task):
        return {
            "success": False,
            "error": "Task must be callable"
        }

    try:
        time.sleep(delay_seconds)
        result = task()

        return {
            "success": True,
            "delay": delay_seconds,
            "result": result,
            "message": f"⏰ Task executed after {delay_seconds} seconds"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
