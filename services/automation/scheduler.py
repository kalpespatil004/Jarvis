"""
services/automation/scheduler.py
----------------------------------
Simple reminder/alarm/task scheduler using Python's schedule library.
"""

import threading
import time
import re
import json
import os
from datetime import datetime, timedelta

try:
    import schedule
    _SCHEDULE = True
except ImportError:
    _SCHEDULE = False

try:
    from config import AUTOMATION_RULES_FILE
except ImportError:
    AUTOMATION_RULES_FILE = "database/automation_rules.json"

_reminders = []
_scheduler_running = False


# ── Helpers ──────────────────────────────────────────────────

def _save_reminders():
    os.makedirs(os.path.dirname(AUTOMATION_RULES_FILE), exist_ok=True)
    with open(AUTOMATION_RULES_FILE, "w") as f:
        json.dump(_reminders, f, indent=2)


def _load_reminders():
    global _reminders
    if os.path.exists(AUTOMATION_RULES_FILE):
        with open(AUTOMATION_RULES_FILE, "r") as f:
            _reminders = json.load(f)


def _parse_time_expression(expr: str) -> datetime | None:
    """Try to parse a natural time expression like '5 minutes', '8pm', 'in 2 hours'."""
    expr = expr.strip().lower()
    now = datetime.now()

    # "in X minutes"
    m = re.search(r"in\s+(\d+)\s+minute", expr)
    if m:
        return now + timedelta(minutes=int(m.group(1)))

    # "in X hours"
    m = re.search(r"in\s+(\d+)\s+hour", expr)
    if m:
        return now + timedelta(hours=int(m.group(1)))

    # "at HH:MM" or "at X pm/am"
    m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", expr)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)
        return target

    return None


def add_reminder(text: str, time_expr: str) -> str:
    """Add a reminder."""
    trigger_time = _parse_time_expression(time_expr)

    entry = {
        "text": text,
        "time_expr": time_expr,
        "trigger_time": trigger_time.isoformat() if trigger_time else None,
        "created_at": datetime.now().isoformat(),
        "triggered": False
    }
    _reminders.append(entry)
    _save_reminders()

    if trigger_time:
        return f"⏰ Reminder set for {trigger_time.strftime('%I:%M %p')}."
    return f"⏰ Reminder noted: {text}"


def get_pending_reminders() -> list:
    now = datetime.now()
    pending = []
    for r in _reminders:
        if r.get("triggered"):
            continue
        t = r.get("trigger_time")
        if t:
            trigger = datetime.fromisoformat(t)
            if trigger <= now:
                pending.append(r)
    return pending


def mark_triggered(reminder: dict):
    reminder["triggered"] = True
    _save_reminders()


def start_scheduler(speak_fn=None):
    """Start background scheduler thread."""
    global _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True
    _load_reminders()

    def loop():
        while _scheduler_running:
            for r in get_pending_reminders():
                msg = f"Reminder: {r['text']}"
                print(f"[SCHEDULER] {msg}")
                if speak_fn:
                    speak_fn(msg)
                mark_triggered(r)
            time.sleep(15)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    print("[SCHEDULER] Reminder scheduler started.")
