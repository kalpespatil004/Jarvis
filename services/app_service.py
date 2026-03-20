"""Desktop application launching helpers."""

from __future__ import annotations

import subprocess
import webbrowser

from brain.response_picker import get_response

_APP_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
}

_BROWSER_APPS = {"chrome", "google chrome", "edge", "microsoft edge"}


def open_application_response(app_name: str | None) -> str:
    if not app_name:
        return get_response("fallback")

    app = app_name.lower().strip()

    if app in _BROWSER_APPS:
        webbrowser.open(_APP_ALIASES[app])
        return get_response("open_app", app)

    executable = _APP_ALIASES.get(app)
    if not executable:
        return f"I don't know how to open {app}."

    try:
        subprocess.Popen(executable)
        return get_response("open_app", app)
    except Exception:
        return f"Failed to open {app}."
