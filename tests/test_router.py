import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_stub_modules(monkeypatch):
    """Stub optional runtime integrations so router can be imported in tests."""
    stubs = {
        "LLM.chatbot": {"chat": lambda prompt: "LLM called"},
        "services.time_date.time_utils": {
            "current_time_only": lambda: "12:00",
            "current_date": lambda date_ref="today": "2026-05-15",
            "current_weekday": lambda date_ref="today": "Friday",
        },
        "services.time_date.timezone": {"convert_timezone": lambda *args, **kwargs: "converted"},
        "system.laptop.app_launcher": {"open_app": lambda app: f"Opening {app}",
            "canonicalize_app_name": lambda name: name},
        "system.laptop.brightness": {
            "set_brightness": lambda level: f"brightness {level}",
            "get_brightness": lambda: "brightness",
            "brightness_up": lambda: "brightness up",
            "brightness_down": lambda: "brightness down",
        },
        "system.laptop.volume": {
            "set_volume": lambda level: f"volume {level}",
            "get_volume": lambda: "volume",
            "volume_up": lambda: "volume up",
            "volume_down": lambda: "volume down",
        },
        "system.laptop.window_manager": {
            "minimize_window": lambda: "minimized",
            "maximize_window": lambda: "maximized",
            "restore_window": lambda: "restored",
            "close_window": lambda: "closed",
            "focus_window": lambda name=None: "focused",
            "move_window": lambda *args, **kwargs: "moved",
            "resize_window": lambda *args, **kwargs: "resized",
        },
        "system.laptop.screenshot": {"take_screenshot": lambda: "screenshot"},
        "system.laptop.run_code": {
            "run_python_file": lambda file=None: "ran python",
            "run_command": lambda command=None: "ran command",
            "open_cmd": lambda: "cmd",
            "open_powershell": lambda: "powershell",
        },
        "system.laptop.file_manager": {
            "create_folder": lambda name=None: "folder created",
            "delete_item": lambda name=None: "deleted",
            "move_file": lambda name=None: "moved file",
            "copy_file": lambda name=None: "copied file",
            "list_files": lambda name=None: "files",
            "create_file": lambda name=None: "file created",
            "search_file": lambda name=None: "found",
            "file_info": lambda name=None: "info",
        },
        "system.laptop.process": {
            "list_processes": lambda: "processes",
            "kill_process_by_name": lambda name=None: "killed",
            "kill_process_by_pid": lambda pid=None: "killed pid",
            "is_process_running": lambda name=None: "running",
        },
        "services.music.music_services": {
            "play_music_response": lambda text="": "playing music",
            "stop_music_response": lambda: "stopped music",
            "next_track_response": lambda: "next track",
            "previous_track_response": lambda: "previous track",
            "play_music_by_mood": lambda mood="": "mood music",
            "play_artist": lambda artist="": "artist music",
            "play_playlist": lambda genre="": "playlist",
            "resume_music_response": lambda: "resumed music",
        },
        "services.youtube.play": {"play_video": lambda video: {"message": "playing video"}},
        "services.youtube.search": {"search_youtube": lambda query: {"message": "searching youtube"}},
        "services.weather.weather_api": {"get_weather": lambda city: {"success": True}},
        "services.weather.formatter": {"format_weather": lambda result: "weather"},
        "services.news.news_api": {"get_news": lambda category="general": {"success": True, "news": []}},
        "services.dictionary.dictionary_api": {"lookup_word": lambda word: {"success": True}},
        "services.dictionary.meanings": {"format_meanings": lambda result: "meaning"},
        "services.crypto.crypto_api": {"get_crypto_price": lambda **kwargs: {"success": False, "error": "stub"}},
        "services.crypto.price_alerts": {"check_price_alert": lambda **kwargs: {"message": "alert"}},
        "services.automation.scheduler": {"schedule_task": lambda *args, **kwargs: None},
    }

    for module_name, attrs in stubs.items():
        module = types.ModuleType(module_name)
        for name, value in attrs.items():
            setattr(module, name, value)
        monkeypatch.setitem(sys.modules, module_name, module)


def _import_router(monkeypatch):
    _install_stub_modules(monkeypatch)
    sys.modules.pop("brain.router", None)
    return importlib.import_module("brain.router")


def test_chat_intent_uses_explicit_response_without_calling_llm(monkeypatch):
    router = _import_router(monkeypatch)

    def fail_llm_chat(prompt):
        raise AssertionError("llm_chat should not be called when response is present")

    monkeypatch.setattr(router, "llm_chat", fail_llm_chat)

    response = router.route(
        {
            "intent": "chat",
            "response": "Do you mean Chrome window or VS Code window?",
            "disambiguation_needed": True,
        },
        return_response=True,
    )

    assert response == "Do you mean Chrome window or VS Code window?"
