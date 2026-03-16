"""
Router
------
Executes actions based on detected intent.

Supports:
- Voice mode  → speaks the response
- UI   mode  → returns text string
"""

import os
import datetime
import webbrowser
import subprocess

from body.speak import speak
from brain.response_picker import get_response
from LLM.chatbot import chat


# ============================================================
def route(intent_data: dict, return_response: bool = False) -> str:
    """
    Route intent to the correct action.
    return_response=True  → return text (UI mode)
    return_response=False → speak text (voice mode)
    """
    intent = intent_data.get("intent", "unknown")

    reply = _dispatch(intent, intent_data)

    if not reply:
        reply = get_response("fallback")

    if return_response:
        return reply

    speak(reply)
    return reply


# ============================================================
# MAIN DISPATCHER
# ============================================================

def _dispatch(intent: str, data: dict) -> str:

    # ── EXIT ──────────────────────────────────────────────────
    if intent == "exit":
        return "Shutting down. Take care."

    # ── TIME & DATE ───────────────────────────────────────────
    if intent == "get_time":
        now = datetime.datetime.now().strftime("%I:%M %p")
        return get_response("get_time", now)

    if intent == "get_date":
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        return get_response("get_date", today)

    if intent == "convert_timezone":
        try:
            from services.time_date.timezone import convert_timezone
            return convert_timezone(
                data.get("time"), data.get("from_tz"), data.get("to_tz")
            )
        except Exception as e:
            return f"Timezone conversion failed: {e}"

    # ── WEATHER ───────────────────────────────────────────────
    if intent == "get_weather":
        try:
            from services.weather.weather_api import get_weather
            from services.weather.formatter import format_weather
            from config import DEFAULT_WEATHER_CITY
            city = data.get("city") or DEFAULT_WEATHER_CITY
            weather = get_weather(city)
            return format_weather(weather)
        except Exception as e:
            return f"Could not fetch weather: {e}"

    # ── NEWS ──────────────────────────────────────────────────
    if intent == "get_news":
        try:
            from services.news.news_api import get_news
            result = get_news(
                category=data.get("category", "general"),
                country="in",
                limit=5
            )
            if not result.get("success"):
                return f"News error: {result.get('error', 'unknown')}"
            articles = result.get("news", [])
            if not articles:
                return "No news articles found right now."
            lines = [f"📰 Top {result['category'].title()} News:"]
            for i, a in enumerate(articles[:5], 1):
                lines.append(f"{i}. {a['title']} — {a['source']}")
            return "\n".join(lines)
        except Exception as e:
            return f"Could not fetch news: {e}"

    # ── CRYPTO ────────────────────────────────────────────────
    if intent == "get_crypto":
        try:
            from services.crypto.crypto_api import get_crypto_price
            result = get_crypto_price(
                symbol=data.get("coin", "bitcoin"),
                currency=data.get("currency", "inr")
            )
            if not result.get("success"):
                return f"Crypto error: {result.get('error', 'unknown')}"
            return (
                f"💰 {result['coin'].title()} ({result['symbol']}) is currently "
                f"{result['price']:,} {result['currency']} "
            )
        except Exception as e:
            return f"Could not fetch crypto price: {e}"

    # ── YOUTUBE ───────────────────────────────────────────────
    if intent == "search_youtube":
        try:
            from services.youtube.search import search_youtube
            result = search_youtube(data.get("query", ""))
            return result.get("message", "Opening YouTube.")
        except Exception as e:
            return f"YouTube search failed: {e}"

    # ── DICTIONARY ────────────────────────────────────────────
    if intent == "dictionary":
        try:
            from services.dictionary.dictionary_api import lookup_word
            from services.dictionary.meanings import format_meanings
            result = lookup_word(data.get("word", ""))
            return format_meanings(result)
        except Exception as e:
            return f"Dictionary lookup failed: {e}"

    # ── OPEN APP ─────────────────────────────────────────────
    if intent == "open_app":
        app = data.get("app", "")
        if not app:
            return get_response("fallback")
        return _open_app(app)

    # ── VOLUME ────────────────────────────────────────────────
    if intent == "volume_up":
        return _safe_import("system.laptop.volume", "volume_up")

    if intent == "volume_down":
        return _safe_import("system.laptop.volume", "volume_down")

    if intent == "set_volume":
        level = data.get("level", 50)
        return _safe_import("system.laptop.volume", "set_volume", level)

    if intent == "get_volume":
        return _safe_import("system.laptop.volume", "get_volume")

    if intent == "mute":
        return _safe_import("system.laptop.volume", "set_volume", 0)

    # ── BRIGHTNESS ────────────────────────────────────────────
    if intent == "brightness_up":
        return _safe_import("system.laptop.brightness", "brightness_up")

    if intent == "brightness_down":
        return _safe_import("system.laptop.brightness", "brightness_down")

    if intent == "set_brightness":
        level = data.get("level", 50)
        return _safe_import("system.laptop.brightness", "set_brightness", level)

    # ── SCREENSHOT ────────────────────────────────────────────
    if intent == "take_screenshot":
        return _safe_import("system.laptop.screenshot", "take_screenshot")

    # ── MUSIC ─────────────────────────────────────────────────
    if intent == "play_music":
        return get_response("play_music")

    if intent == "stop_music":
        _stop_music()
        return get_response("stop_music")

    # ── WINDOW MANAGEMENT ─────────────────────────────────────
    if intent == "minimize_window":
        return _safe_import("system.laptop.window_manager", "minimize_window")

    if intent == "maximize_window":
        return _safe_import("system.laptop.window_manager", "maximize_window")

    if intent == "close_window":
        return _safe_import("system.laptop.window_manager", "close_window")

    if intent == "restore_window":
        return _safe_import("system.laptop.window_manager", "restore_window")

    # ── PROCESSES ─────────────────────────────────────────────
    if intent == "list_processes":
        return _safe_import("system.laptop.process", "list_processes")

    if intent == "kill_process":
        name = data.get("process", "")
        return _safe_import("system.laptop.process", "kill_process_by_name", name)

    # ── FILE MANAGER ─────────────────────────────────────────
    if intent == "list_files":
        return _safe_import("system.laptop.file_manager", "list_files")

    if intent == "create_folder":
        return _safe_import("system.laptop.file_manager", "create_folder", data.get("name", "new_folder"))

    if intent == "delete_item":
        return _safe_import("system.laptop.file_manager", "delete_item", data.get("name", ""))

    if intent == "search_file":
        return _safe_import("system.laptop.file_manager", "search_file", data.get("name", ""))

    # ── RUN CODE ─────────────────────────────────────────────
    if intent == "run_command":
        cmd = data.get("command", "")
        if cmd:
            return _safe_import("system.laptop.run_code", "run_command", cmd)
        return _safe_import("system.laptop.run_code", "open_cmd")

    # ── LOCATION ─────────────────────────────────────────────
    if intent == "get_location":
        return _safe_import("system.mobile.gps", "get_location")

    # ── SEND SMS ─────────────────────────────────────────────
    if intent == "send_sms":
        return _safe_import("system.mobile.messaging", "send_sms",
                            data.get("to", ""), data.get("message", ""))

    # ── NOTIFICATIONS ────────────────────────────────────────
    if intent == "read_notifications":
        return _safe_import("system.mobile.notifications", "read_notification", "all")

    # ── SYSTEM INFO ──────────────────────────────────────────
    if intent == "system_info":
        return _get_system_info()

    # ── CALCULATOR ───────────────────────────────────────────
    if intent == "calculate":
        return _calculate(data.get("expression", ""))

    # ── VAULT ────────────────────────────────────────────────
    if intent in ("vault_open", "vault_store", "vault_retrieve"):
        return _handle_vault(intent, data)

    # ── MEMORY / RECALL ──────────────────────────────────────
    if intent == "recall_memory":
        try:
            from memory.memory_retriver import recall_recent
            history = recall_recent(5)
            if not history:
                return "I don't have any recent conversation history."
            lines = ["🧠 Recent Memory:"]
            for msg in history:
                lines.append(f"  [{msg['role'].upper()}] {msg['text']}")
            return "\n".join(lines)
        except Exception as e:
            return f"Memory recall failed: {e}"

    if intent == "save_memory":
        try:
            from memory.conversation import add_message
            add_message("note", data.get("content", ""))
            return "Got it. I'll remember that."
        except Exception:
            return "I tried to remember, but something went wrong."

    # ── REMINDER / ALARM / TASK ──────────────────────────────
    if intent in ("set_reminder", "set_alarm", "schedule_task"):
        return _handle_automation(intent, data)

    # ── CHAT / GENERAL ───────────────────────────────────────
    if intent in ("chat", "unknown"):
        query = data.get("text", "")
        if not query:
            return get_response("fallback")
        # Inject memory context
        context_prefix = _build_context_prefix()
        full_prompt = (context_prefix + query) if context_prefix else query
        reply = chat(full_prompt)
        # Save to memory
        try:
            from memory.conversation import add_message
            add_message("user", query)
            add_message("jarvis", reply)
        except Exception:
            pass
        return reply

    return get_response("fallback")


# ============================================================
# HELPERS
# ============================================================

def _safe_import(module: str, func: str, *args):
    """Safely import and call a function, returning error string on failure."""
    try:
        import importlib
        mod = importlib.import_module(module)
        fn = getattr(mod, func)
        return fn(*args) if args else fn()
    except ImportError:
        return f"Module {module} not available on this platform."
    except Exception as e:
        return f"Error: {e}"


def _open_app(app: str) -> str:
    app = app.lower()
    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "chrome": None,
        "edge": None,
        "firefox": None,
    }
    browsers = {"chrome", "edge", "firefox"}
    if app in browsers:
        try:
            webbrowser.open(app)
            return get_response("open_app", app)
        except Exception:
            return f"Could not open {app}."
    exe = app_map.get(app)
    if exe:
        try:
            subprocess.Popen(exe)
            return get_response("open_app", app)
        except Exception as e:
            return f"Failed to open {app}: {e}"
    # Generic attempt via system launcher
    try:
        if os.name == "nt":
            subprocess.Popen(f"start {app}", shell=True)
        else:
            subprocess.Popen(["xdg-open", app])
        return get_response("open_app", app)
    except Exception:
        return f"I don't know how to open {app}."


def _stop_music():
    players = ["wmplayer.exe", "vlc.exe", "spotify.exe"]
    for player in players:
        if os.name == "nt":
            os.system(f"taskkill /im {player} /f >nul 2>&1")
        else:
            os.system(f"pkill -f {player.replace('.exe', '')} 2>/dev/null")


def _get_system_info() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        lines = [
            "💻 System Status:",
            f"  CPU Usage  : {cpu}%",
            f"  RAM Used   : {ram.percent}% ({ram.used // (1024**2)} MB / {ram.total // (1024**2)} MB)",
            f"  Disk Used  : {disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)",
        ]
        try:
            battery = psutil.sensors_battery()
            if battery:
                lines.append(f"  Battery    : {battery.percent:.0f}% {'🔌 Charging' if battery.power_plugged else '🔋'}")
        except Exception:
            pass
        return "\n".join(lines)
    except ImportError:
        return "psutil not installed. Cannot fetch system info."
    except Exception as e:
        return f"System info error: {e}"


def _calculate(expr: str) -> str:
    if not expr:
        return "Please provide an expression to calculate."
    try:
        import sympy
        result = sympy.sympify(expr.replace("^", "**"))
        return f"🧮 {expr} = {result}"
    except Exception:
        try:
            # Safe eval fallback
            allowed = set("0123456789+-*/.() ")
            if all(c in allowed for c in expr):
                result = eval(expr, {"__builtins__": {}})  # noqa: S307
                return f"🧮 {expr} = {result}"
        except Exception:
            pass
        return f"Could not calculate: {expr}"


def _handle_vault(intent: str, data: dict) -> str:
    try:
        from vault.vault_manager import store_document, retrieve_document, list_documents
        if intent == "vault_store":
            item = data.get("item", "")
            return store_document(item, item)
        elif intent == "vault_retrieve":
            item = data.get("item", "")
            return retrieve_document(item)
        else:
            docs = list_documents()
            if not docs:
                return "🔐 Your vault is empty."
            return "🔐 Vault Documents:\n" + "\n".join(f"  • {d}" for d in docs)
    except ImportError:
        return "Vault module not available."
    except Exception as e:
        return f"Vault error: {e}"


def _handle_automation(intent: str, data: dict) -> str:
    try:
        from services.automation.scheduler import add_reminder
        details = data.get("details", "")
        time_expr = data.get("time_expr", "")
        result = add_reminder(details, time_expr)
        return result
    except ImportError:
        return f"Automation module loading. Your {intent.replace('_', ' ')} noted: {data.get('details', '')}"
    except Exception as e:
        return f"Could not set {intent}: {e}"


def _build_context_prefix() -> str:
    """Build a short context string from recent conversation history."""
    try:
        from memory.memory_retriver import recall_recent
        from config import MEMORY_CONTEXT_WINDOW
        history = recall_recent(MEMORY_CONTEXT_WINDOW)
        if not history:
            return ""
        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Jarvis"
            lines.append(f"{role}: {msg['text']}")
        return "[Context]\n" + "\n".join(lines) + "\n[Current]\n"
    except Exception:
        return ""
