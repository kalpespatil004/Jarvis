"""
router.py
---------
Routes detected intents to the correct service/module.

Brain decides WHAT to do.
Router decides WHO handles it.
"""

from __future__ import annotations

import threading

from brain.response_picker import get_response

# ── LLM Chat ─────────────────────────────────
from LLM.chatbot import chat as llm_chat

# ── Time & Date ───────────────────────────────
from services.time_date.time_utils import current_time_only, current_date
from services.time_date.timezone import convert_timezone

# ── System ────────────────────────────────────
from system.laptop.app_launcher import open_app                          # FIXED: was open_application
from system.laptop.brightness import set_brightness
from system.laptop.volume import set_volume
from system.laptop.window_manager import minimize_window, maximize_window, close_window
from system.laptop.screenshot import take_screenshot
from system.laptop.run_code import run_python_file
from system.laptop.file_manager import create_folder, delete_item, move_file, copy_file
from system.laptop.process import list_processes, kill_process_by_name

# ── Music ─────────────────────────────────────
from services.music_service import play_music_response, stop_music_response

# ── YouTube ───────────────────────────────────
from services.youtube.play import play_video
from services.youtube.search import search_youtube

# ── Weather ───────────────────────────────────
from services.weather.weather_api import get_weather
from services.weather.formatter import format_weather

# ── News ──────────────────────────────────────
from services.news.news_api import get_news

# ── Dictionary ────────────────────────────────
from services.dictionary.dictionary_api import lookup_word
from services.dictionary.meanings import format_meanings

# ── Crypto ────────────────────────────────────
from services.crypto.crypto_api import get_crypto_price
from services.crypto.price_alerts import check_price_alert

# ── Automation ────────────────────────────────
from services.automation.scheduler import schedule_task


# =========================
# ROUTER
# =========================
def route(intent_data: dict, return_response: bool = False) -> str:
    """
    Route intent to the correct service.

    If return_response=True → returns text (UI/API mode).
    Otherwise → speaks the response (voice mode).
    """

    intent = intent_data.get("intent", "unknown")
    reply = ""

    # ─────────────────────────────────────────
    # CORE
    # ─────────────────────────────────────────
    if intent == "exit":
        reply = "Shutting down, sir."

    elif intent == "greeting":
        reply = "Hello sir, how can I help you?"

    # ─────────────────────────────────────────
    # CHAT / LLM FALLBACK                          ← FIXED: was missing
    # ─────────────────────────────────────────
    elif intent == "chat":
        reply = llm_chat(intent_data.get("text", ""))

    # ─────────────────────────────────────────
    # TIME & DATE                                  ← FIXED: were missing
    # ─────────────────────────────────────────
    elif intent == "get_time":
        reply = f"Current time is {current_time_only()}."

    elif intent == "get_date":
        reply = f"Today's date is {current_date()}."

    elif intent == "advice_time":
        reply = llm_chat(intent_data.get("topic", intent_data.get("text", "")))

    elif intent == "convert_timezone":
        # Pass raw query to LLM — timezone parsing needs NLP
        reply = llm_chat(intent_data.get("query", intent_data.get("text", "")))

    # ─────────────────────────────────────────
    # WEATHER
    # ─────────────────────────────────────────
    elif intent == "get_weather":
        city = intent_data.get("city") or "Pune"
        result = get_weather(city)
        reply = format_weather(result)

    # ─────────────────────────────────────────
    # NEWS
    # ─────────────────────────────────────────
    elif intent == "get_news":
        category = intent_data.get("category", "general")
        result = get_news(category=category)
        if result.get("success"):
            articles = result.get("news", [])
            if articles:
                lines = [f"📰 Top {category.capitalize()} News:"]
                for i, a in enumerate(articles, 1):
                    lines.append(f"{i}. {a['title']} — {a['source']}")
                reply = "\n".join(lines)
            else:
                reply = "No news articles found right now."
        else:
            reply = f"Could not fetch news: {result.get('error')}"

    # ─────────────────────────────────────────
    # DICTIONARY
    # ─────────────────────────────────────────
    elif intent == "lookup_word":
        word = intent_data.get("word")
        if not word:
            reply = "Please tell me which word to look up."
        else:
            result = lookup_word(word)
            reply = format_meanings(result)

    # ─────────────────────────────────────────
    # CRYPTO PRICE
    # ─────────────────────────────────────────
    elif intent == "get_crypto_price":
        symbol = intent_data.get("symbol", "bitcoin")
        currency = intent_data.get("currency", "inr")
        result = get_crypto_price(symbol=symbol, currency=currency)
        if result.get("success"):
            reply = (
                f"💰 {result['coin'].capitalize()} ({result['symbol']}) "
                f"is {result['price']:,} {result['currency']}"
            )
        else:
            reply = f"Could not fetch price: {result.get('error')}"

    # ─────────────────────────────────────────
    # CRYPTO PRICE ALERT
    # ─────────────────────────────────────────
    elif intent == "check_price_alert":
        target = intent_data.get("target_price")
        direction = intent_data.get("direction", "above")
        symbol = intent_data.get("symbol", "bitcoin")
        currency = intent_data.get("currency", "inr")

        if target is None:
            reply = "Please specify a target price for the alert."
        else:
            price_data = get_crypto_price(symbol=symbol, currency=currency)
            if price_data.get("success"):
                result = check_price_alert(
                    current_price=price_data["price"],
                    target_price=target,
                    direction=direction
                )
                reply = result.get("message", "Alert checked.")
            else:
                reply = f"Could not fetch price: {price_data.get('error')}"

    # ─────────────────────────────────────────
    # YOUTUBE                                      ← FIXED: added missing handlers
    # ─────────────────────────────────────────
    elif intent == "play_youtube":
        video = intent_data.get("video", "")
        if not video:
            reply = "Please tell me what to play on YouTube."
        else:
            result = play_video(video)
            reply = result.get("message", "Opening YouTube.")

    elif intent == "search_youtube":
        query = intent_data.get("query", "")
        if not query:
            reply = "Please tell me what to search on YouTube."
        else:
            result = search_youtube(query)
            reply = result.get("message", "Searching YouTube.")

    # ─────────────────────────────────────────
    # MUSIC                                        ← FIXED: were missing
    # ─────────────────────────────────────────
    elif intent == "play_music":
        reply = play_music_response()

    elif intent == "stop_music":
        reply = stop_music_response()

    # ─────────────────────────────────────────
    # APP LAUNCHER                                 ← FIXED: open_application → open_app
    # ─────────────────────────────────────────
    elif intent == "open_app":
        app = intent_data.get("app")
        if not app:
            reply = "Which app should I open?"
        else:
            reply = open_app(app)

    # ─────────────────────────────────────────
    # BRIGHTNESS
    # ─────────────────────────────────────────
    elif intent == "brightness_control":
        level = intent_data.get("level")
        if level is not None:
            reply = set_brightness(level)
        else:
            reply = "Please specify a brightness level between 0 and 100."

    # ─────────────────────────────────────────
    # VOLUME
    # ─────────────────────────────────────────
    elif intent == "volume_control":
        level = intent_data.get("level")
        if level is not None:
            reply = set_volume(level)
        else:
            reply = "Please specify a volume level between 0 and 100."

    # ─────────────────────────────────────────
    # WINDOW CONTROL
    # ─────────────────────────────────────────
    elif intent == "window_control":
        action = intent_data.get("action", "")
        if action == "minimize":
            reply = minimize_window()
        elif action == "maximize":
            reply = maximize_window()
        elif action == "close":
            reply = close_window()
        else:
            reply = "Unknown window action."

    # ─────────────────────────────────────────
    # SCREENSHOT
    # ─────────────────────────────────────────
    elif intent == "screenshot":
        reply = take_screenshot()

    # ─────────────────────────────────────────
    # RUN CODE
    # ─────────────────────────────────────────
    elif intent == "run_code":
        file = intent_data.get("file", "")
        if not file:
            reply = "Please specify a Python file to run."
        else:
            reply = run_python_file(file)

    # ─────────────────────────────────────────
    # FILE MANAGER
    # ─────────────────────────────────────────
    elif intent == "file_manager":
        action = intent_data.get("action", "")
        name = intent_data.get("name", "")
        destination = intent_data.get("destination", "")

        if action == "create_folder":
            reply = create_folder(name)
        elif action == "delete":
            reply = delete_item(name)
        elif action == "move":
            reply = move_file(name, destination)
        elif action == "copy":
            reply = copy_file(name, destination)
        else:
            reply = f"Unknown file action: {action}"

    # ─────────────────────────────────────────
    # PROCESS MANAGER
    # ─────────────────────────────────────────
    elif intent == "process_manager":
        action = intent_data.get("action", "")
        name = intent_data.get("name", "")

        if action == "list":
            reply = list_processes()
        elif action == "kill":
            if not name:
                reply = "Please specify a process name to kill."
            else:
                reply = kill_process_by_name(name)
        else:
            reply = f"Unknown process action: {action}"

    # ─────────────────────────────────────────
    # SCHEDULE TASK / REMINDER
    # ─────────────────────────────────────────
    elif intent == "schedule_task":
        delay = intent_data.get("delay_seconds", 0)
        query = intent_data.get("query", "Your reminder is up.")
        reply = f"⏰ Reminder set for {delay} seconds."

        def _reminder():
            from body.speak import speak
            speak(f"Reminder: {query}")

        threading.Thread(
            target=schedule_task,
            args=(delay, _reminder),
            daemon=True
        ).start()

    # ─────────────────────────────────────────
    # AUTOMATION                                   ← FIXED: were missing
    # ─────────────────────────────────────────
    elif intent == "evaluate_trigger":
        reply = llm_chat(intent_data.get("query", intent_data.get("text", "")))

    elif intent == "apply_rules":
        reply = llm_chat(intent_data.get("query", intent_data.get("text", "")))

    # ─────────────────────────────────────────
    # UNKNOWN FALLBACK
    # ─────────────────────────────────────────
    else:
        text = intent_data.get("text", "")
        reply = llm_chat(text) if text else get_response("fallback")

    # ─────────────────────────────────────────
    # RESPOND
    # ─────────────────────────────────────────
    if not reply:
        reply = get_response("fallback")

    if return_response:
        return reply

    from body.speak import speak
    speak(reply)

    if intent == "exit":
        raise SystemExit

    return reply