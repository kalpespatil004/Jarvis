import difflib
import os
import platform
import subprocess

# Optional: predefined paths for common apps
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "notepad": r"C:\Windows\system32\notepad.exe",
    "calculator": r"C:\Windows\System32\calc.exe",
    "cmd": r"C:\Windows\system32\cmd.exe",
    "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    "paint": r"C:\Windows\system32\mspaint.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
}

# Aliases and common typos → canonical key in APP_PATHS or name for `start`.
APP_ALIASES = {
    "browser": "chrome",
    "web browser": "chrome",
    "internet browser": "chrome",
    "google chrome": "chrome",
    "chorme": "chrome",
    "chrom": "chrome",
    "chrime": "chrome",
    "microsoft edge": "edge",
    "edge browser": "edge",
}


def _known_app_names() -> list[str]:
    return sorted(set(APP_PATHS.keys()) | set(APP_ALIASES.values()))


def canonicalize_app_name(name: str) -> str:
    """Map user phrasing / typos to a canonical app token used by APP_PATHS and `start`."""
    if not name:
        return name
    n = name.lower().strip()
    if not n:
        return n
    if n in APP_ALIASES:
        return APP_ALIASES[n]
    for alias, canonical in sorted(APP_ALIASES.items(), key=lambda x: -len(x[0])):
        if n == alias:
            return canonical
        if n.startswith(alias + " ") or n.endswith(" " + alias):
            return canonical
    pool = _known_app_names()
    matches = difflib.get_close_matches(n, pool, n=1, cutoff=0.72)
    if matches:
        return matches[0]
    return n


def open_app(name):
    """
    Open any app by name.
    1. Try predefined path
    2. Try 'start' command (Windows)
    """
    name = canonicalize_app_name(name)

    # 1️⃣ Try predefined path
    path = APP_PATHS.get(name)
    if path and os.path.exists(path):
        try:
            subprocess.Popen(path)
            return f"✅ Opening {name}"
        except Exception as e:
            return f"❌ Failed to open {name}: {e}"

    # 2️⃣ Try 'start' command for any app in PATH
    if platform.system() == "Windows":
        try:
            subprocess.Popen(f"start {name}", shell=True)
            return f"✅ Trying to open {name}"
        except Exception as e:
            return f"❌ Failed to open {name} using start command: {e}"

    return f"❌ App not found: {name}"
