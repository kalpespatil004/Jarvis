from __future__ import annotations

import difflib
import json
import os
import platform
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

APP_INDEX_PATH = Path("database/app_names.json")
CACHE_TTL_HOURS = 24

# Optional: predefined paths for common apps
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "code": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
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
    "terminal": "cmd",
    "vs code": "vscode",
    "visual studio code": "vscode",
    "code editor": "vscode",
    "settings": "windows_settings",
    "windows settings": "windows_settings",
    "whatsapp": "whatsapp",
}

APP_SPECIAL_URIS = {
    "windows_settings": "ms-settings:",
}


def _normalize_key(name: str) -> str:
    return " ".join((name or "").lower().strip().split())


def _tag_for_name(name: str) -> str:
    n = _normalize_key(name)
    if any(k in n for k in ("chrome", "edge", "firefox", "browser")):
        return "browser"
    if any(k in n for k in ("vscode", "visual studio", "pycharm", "intellij", "code")):
        return "dev"
    if any(k in n for k in ("steam", "epic", "game", "valorant", "minecraft")):
        return "game"
    if any(k in n for k in ("spotify", "vlc", "music", "player", "whatsapp")):
        return "media"
    if any(k in n for k in ("word", "excel", "powerpoint", "office")):
        return "productivity"
    return "utility"


def _known_app_names() -> list[str]:
    names = set(APP_PATHS.keys()) | set(APP_ALIASES.keys()) | set(APP_ALIASES.values())
    for item in load_app_index().get("apps", []):
        name = item.get("name")
        if isinstance(name, str):
            names.add(_normalize_key(name))
    return sorted(names)


def canonicalize_app_name(name: str) -> str:
    """Map user phrasing / typos to a canonical app token used by APP_PATHS and index lookup."""
    n = _normalize_key(name)
    if not n:
        return n
    if n in APP_ALIASES:
        return APP_ALIASES[n]
    for alias, canonical in sorted(APP_ALIASES.items(), key=lambda x: -len(x[0])):
        if n == alias or n.startswith(alias + " ") or n.endswith(" " + alias):
            return canonical
    pool = _known_app_names()
    matches = difflib.get_close_matches(n, pool, n=1, cutoff=0.72)
    return matches[0] if matches else n


def _run_powershell_json(command: str) -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        parsed = json.loads(completed.stdout)
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        return []
    return []


def _collect_registry_apps() -> list[dict[str, Any]]:
    if platform.system() != "Windows":
        return []
    cmd = (
        "$paths=@('HKLM:\\Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\*',"
        "'HKLM:\\Software\\\\WOW6432Node\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\*',"
        "'HKCU:\\Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\*');"
        "$apps=Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
        "Where-Object {$_.DisplayName} | "
        "Select-Object DisplayName,DisplayIcon,InstallLocation,Publisher;"
        "$apps | ConvertTo-Json -Depth 3"
    )
    rows = _run_powershell_json(cmd)
    results: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("DisplayName") or "").strip()
        if not name:
            continue
        location = str(row.get("InstallLocation") or row.get("DisplayIcon") or "").strip().strip('"')
        results.append(
            {
                "name": name,
                "location": location,
                "source": "registry",
                "tag": _tag_for_name(name),
            }
        )
    return results


def _collect_program_files_apps() -> list[dict[str, Any]]:
    if platform.system() != "Windows":
        return []
    roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")]
    roots = [r for r in roots if r]
    results: list[dict[str, Any]] = []
    for root in roots:
        for base, _, files in os.walk(root):
            depth = Path(base).relative_to(root).parts
            if len(depth) > 4:
                continue
            for file_name in files:
                if not file_name.lower().endswith(".exe"):
                    continue
                if file_name.lower() in {"uninstall.exe", "setup.exe", "update.exe"}:
                    continue
                full_path = str(Path(base) / file_name)
                app_name = Path(file_name).stem
                results.append(
                    {
                        "name": app_name,
                        "location": full_path,
                        "source": "program_files",
                        "tag": _tag_for_name(app_name),
                    }
                )
    return results


def _collect_uwp_apps() -> list[dict[str, Any]]:
    if platform.system() != "Windows":
        return []
    cmd = "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Depth 3"
    rows = _run_powershell_json(cmd)
    results: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("Name") or "").strip()
        appid = str(row.get("AppID") or "").strip()
        if not name:
            continue
        results.append(
            {
                "name": name,
                "location": appid,
                "source": "uwp",
                "tag": _tag_for_name(name),
            }
        )
    return results


def _dedupe_apps(apps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for app in apps:
        name = _normalize_key(str(app.get("name", "")))
        location = str(app.get("location", "")).strip()
        if not name:
            continue
        key = (name, location.lower())
        if key in deduped:
            continue
        deduped[key] = {
            "name": name,
            "location": location,
            "source": app.get("source", "unknown"),
            "tag": app.get("tag", _tag_for_name(name)),
        }
    return sorted(deduped.values(), key=lambda item: item["name"])


def build_app_index(force_refresh: bool = False) -> dict[str, Any]:
    """
    Build an app index from registry + Program Files + UWP Start menu.
    Writes `database/app_names.json` and returns the payload.
    """
    existing = load_app_index()
    if not force_refresh and existing.get("apps") and not _cache_expired(existing):
        return existing

    apps = []
    apps.extend(_collect_registry_apps())
    apps.extend(_collect_program_files_apps())
    apps.extend(_collect_uwp_apps())

    # Always keep curated paths as strongest records.
    for name, location in APP_PATHS.items():
        apps.append({"name": name, "location": location, "source": "builtin", "tag": _tag_for_name(name)})

    deduped = _dedupe_apps(apps)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "count": len(deduped),
        "apps": deduped,
    }

    APP_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    APP_INDEX_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_app_index() -> dict[str, Any]:
    if not APP_INDEX_PATH.exists():
        return {}
    try:
        return json.loads(APP_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _cache_expired(payload: dict[str, Any]) -> bool:
    generated = payload.get("generated_at")
    if not generated:
        return True
    try:
        generated_dt = datetime.fromisoformat(str(generated).replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) - generated_dt > timedelta(hours=CACHE_TTL_HOURS)


def search_apps(query: str, *, limit: int = 10, tag: str | None = None) -> list[dict[str, Any]]:
    payload = build_app_index(force_refresh=False)
    apps = payload.get("apps", [])
    if not isinstance(apps, list):
        return []

    q = canonicalize_app_name(query)
    if tag:
        apps = [a for a in apps if str(a.get("tag", "")).lower() == tag.lower()]

    exact = [a for a in apps if _normalize_key(str(a.get("name", ""))) == q]
    if exact:
        return exact[:limit]

    contains = [a for a in apps if q in _normalize_key(str(a.get("name", "")))]
    if contains:
        return contains[:limit]

    names = [_normalize_key(str(a.get("name", ""))) for a in apps]
    matched = difflib.get_close_matches(q, names, n=limit, cutoff=0.62)
    ranked = [a for a in apps if _normalize_key(str(a.get("name", ""))) in matched]
    return ranked[:limit]


def resolve_app(query: str) -> dict[str, Any] | None:
    results = search_apps(query, limit=1)
    return results[0] if results else None


def open_app(name: str) -> str:
    """
    Open any app by name.
    1. Resolve by indexed app location (`database/app_names.json`)
    2. Fallback to predefined paths
    3. Fallback to `start` command (Windows)
    """
    canonical = canonicalize_app_name(name)

    if canonical in APP_SPECIAL_URIS and platform.system() == "Windows":
        uri = APP_SPECIAL_URIS[canonical]
        try:
            subprocess.Popen(f'start "" {uri}', shell=True)
            return f"✅ Opening {canonical}"
        except Exception as e:
            return f"❌ Failed to open {canonical}: {e}"

    resolved = resolve_app(canonical)

    if resolved:
        location = os.path.expandvars(str(resolved.get("location", "")).strip())
        app_name = resolved.get("name", canonical)

        # UWP AppID launch
        if location and "!" in location and platform.system() == "Windows":
            try:
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{location}"])
                return f"✅ Opening {app_name}"
            except Exception:
                pass

        # Classic executable path launch
        if location and os.path.exists(location):
            try:
                subprocess.Popen(location)
                return f"✅ Opening {app_name}"
            except Exception as e:
                return f"❌ Failed to open {app_name}: {e}"

    # predefined fallback
    path = APP_PATHS.get(canonical)
    path = os.path.expandvars(path) if path else None
    if path and os.path.exists(path):
        try:
            subprocess.Popen(path)
            return f"✅ Opening {canonical}"
        except Exception as e:
            return f"❌ Failed to open {canonical}: {e}"

    if platform.system() == "Windows":
        try:
            subprocess.Popen(f'start "" {canonical}', shell=True)
            return f"✅ Trying to open {canonical}"
        except Exception as e:
            return f"❌ Failed to open {canonical} using start command: {e}"

    return f"❌ App not found: {canonical}"
