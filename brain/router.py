from __future__ import annotations
import threading

from brain.response_picker import get_response

# ── SYSTEM ───────────────────────────────────
from system.laptop.app_launcher import open_application
from system.laptop.brightness import set_brightness
from system.laptop.volume import set_volume
from system.laptop.window_manager import minimize_window, maximize_window, close_window
from system.laptop.screenshot import take_screenshot
from system.laptop.run_code import run_python_file
from system.laptop.file_manager import create_folder, delete_item, move_file, copy_file
from system.laptop.process import list_processes, kill_process_by_name

# ── YOUTUBE ──────────────────────────────────
from services.youtube.play import play_video
from services.youtube.search import search_youtube

# ── WEATHER ──────────────────────────────────
from services.weather.weather_api import get_weather
from services.weather.formatter import format_weather

# ── NEWS ─────────────────────────────────────
from services.news.news_api import get_news

# ── DICTIONARY ───────────────────────────────
from services.dictionary.dictionary_api import lookup_word
from services.dictionary.meanings import format_meanings

# ── CRYPTO ───────────────────────────────────
from services.crypto.crypto_api import get_crypto_price

# ── AUTOMATION ───────────────────────────────
from services.automation.scheduler import schedule_task


# =========================
# ROUTER
# =========================
def route(intent_data: dict, return_response: bool = False) -> str:

    intent = intent_data.get("intent", "unknown")
    reply = ""

    # ───────── CORE ─────────
    if intent == "exit":
        reply = "Shutting down."

    elif intent == "greeting":
        reply = "Hello."

    # ───────── WEATHER ─────────
    elif intent == "get_weather":
        city = intent_data.get("city", "Pune")
        result = get_weather(city)
        reply = format_weather(result)

    # ───────── NEWS ─────────
    elif intent == "get_news":
        result = get_news()

        if result.get("success"):
            articles = result.get("news", [])
            if articles:
                reply = "\n".join(
                    [f"{i+1}. {a['title']}" for i, a in enumerate(articles[:5])]
                )
            else:
                reply = "No news found."
        else:
            reply = "Failed to fetch news."

    # ───────── DICTIONARY ─────────
    elif intent == "lookup_word":
        word = intent_data.get("word")

        if not word:
            reply = "Tell me a word."
        else:
            result = lookup_word(word)
            reply = format_meanings(result)

    # ───────── CRYPTO ─────────
    elif intent == "get_crypto_price":
        symbol = intent_data.get("symbol", "bitcoin")
        result = get_crypto_price(symbol=symbol)

        if result.get("success"):
            reply = f"{symbol} price is {result['price']}"
        else:
            reply = "Failed to fetch crypto price."

    # ───────── YOUTUBE ─────────
    elif intent == "play_youtube":
        video = intent_data.get("video", "")
        reply = play_video(video).get("message", "Opening YouTube")

    elif intent == "search_youtube":
        query = intent_data.get("query", "")
        reply = search_youtube(query).get("message", "Searching YouTube")

    # ───────── SYSTEM: APP ─────────
    elif intent == "open_app":
        reply = open_application(intent_data.get("app"))

    # ───────── SYSTEM: BRIGHTNESS ─────────
    elif intent == "brightness_control":
        level = intent_data.get("level")
        if level is not None:
            reply = set_brightness(level)
        else:
            reply = "Specify brightness level."

    # ───────── SYSTEM: VOLUME ─────────
    elif intent == "volume_control":
        level = intent_data.get("level")
        if level is not None:
            reply = set_volume(level)
        else:
            reply = "Specify volume level."

    # ───────── SYSTEM: WINDOW ─────────
    elif intent == "window_control":
        action = intent_data.get("action")

        if action == "minimize":
            reply = minimize_window()
        elif action == "maximize":
            reply = maximize_window()
        elif action == "close":
            reply = close_window()
        else:
            reply = "Unknown window action."

    # ───────── SYSTEM: SCREENSHOT ─────────
    elif intent == "screenshot":
        reply = take_screenshot()

    # ───────── SYSTEM: RUN CODE ─────────
    elif intent == "run_code":
        file = intent_data.get("file")
        if file:
            reply = run_python_file(file)
        else:
            reply = "Specify file to run."

    # ───────── FILE MANAGER ─────────
    elif intent == "file_manager":
        action = intent_data.get("action")
        name = intent_data.get("name")
        dest = intent_data.get("destination")

        if action == "create_folder":
            reply = create_folder(name)
        elif action == "delete":
            reply = delete_item(name)
        elif action == "move":
            reply = move_file(name, dest)
        elif action == "copy":
            reply = copy_file(name, dest)
        else:
            reply = "Unknown file action."

    # ───────── PROCESS ─────────
    elif intent == "process_manager":
        action = intent_data.get("action")
        name = intent_data.get("name")

        if action == "list":
            reply = list_processes()
        elif action == "kill":
            reply = kill_process_by_name(name)
        else:
            reply = "Unknown process action."

    # ───────── AUTOMATION ─────────
    elif intent == "schedule_task":
        delay = intent_data.get("delay_seconds", 5)
        query = intent_data.get("query", "Reminder")

        reply = f"Reminder set for {delay} seconds."

        def _reminder():
            from body.speak import speak
            speak(query)

        threading.Thread(
            target=schedule_task,
            args=(delay, _reminder),
            daemon=True
        ).start()

    # ───────── FALLBACK ─────────
    else:
        reply = "I didn't understand that."

    # ───────── FINAL RESPONSE ─────────
    if not reply:
        reply = get_response("fallback")

    if return_response:
        return reply

    from body.speak import speak
    speak(reply)

    if intent == "exit":
        raise SystemExit

    return reply