"""
Hybrid TTS router for Jarvis.

- Online: use ``body.speak_edgetts`` (edge-tts backend)
- Offline: use ``body.speak_TTS`` (simple pyttsx3 backend)
"""

from __future__ import annotations
import importlib
import socket
import sys
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Optional
import re
import unicodedata
import contextlib
import io
import logging

# Suppress logs
logging.getLogger("TTS").setLevel(logging.ERROR)

# Repo root must be on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_state_lock = threading.Lock()
_backend_name: Optional[str] = None
_backend_module: Optional[ModuleType] = None
_warmup_done = {"edge": False, "offline": False}

_connectivity_cache_ttl_s = 5.0
_last_connectivity_check = 0.0
_last_connectivity_result = False


def _internet_available(timeout_s: float = 1.0) -> bool:
    """Quick internet check with short-lived cache."""
    global _last_connectivity_check, _last_connectivity_result
    now = time.monotonic()
    if now - _last_connectivity_check < _connectivity_cache_ttl_s:
        return _last_connectivity_result

    ok = False
    try:
        for dns in ["8.8.8.8", "1.1.1.1", "9.9.9.9"]:
            try:
                with socket.create_connection((dns, 53), timeout=timeout_s):
                    ok = True
                    break
            except OSError:
                continue
    except Exception:
        ok = False

    _last_connectivity_check = now
    _last_connectivity_result = ok
    return ok


def _import_backend(name: str) -> ModuleType:
    """Import backend module with suppressed output."""
    if name == "edge":
        with contextlib.redirect_stdout(io.StringIO()):
            module = importlib.import_module("body.speak_edgetts")
        return module
    return importlib.import_module("body.speak_TTS")


def _get_backend() -> tuple[str, ModuleType]:
    """Choose backend dynamically."""
    global _backend_name, _backend_module

    preferred = "edge" if _internet_available() else "offline"

    with _state_lock:
        if _backend_name == preferred and _backend_module is not None:
            return _backend_name, _backend_module

        try:
            module = _import_backend(preferred)
            chosen = preferred
        except Exception as exc:
            if preferred == "edge":
                print(f"[TTS] Edge unavailable, falling back offline: {exc}")
                try:
                    module = _import_backend("offline")
                    chosen = "offline"
                except Exception as offline_exc:
                    print(f"[TTS] Offline also failed: {offline_exc}")
                    return _get_dummy_backend()
            else:
                print(f"[TTS] Offline failed: {exc}")
                try:
                    module = _import_backend("edge")
                    chosen = "edge"
                except Exception:
                    return _get_dummy_backend()

        if chosen != _backend_name:
            print(f"[TTS] Using backend: {chosen}")

        _backend_name = chosen
        _backend_module = module
        return chosen, module


def _get_dummy_backend() -> tuple[str, ModuleType]:
    """Return a dummy backend that does nothing."""
    class DummyBackend:
        def speak(self, text): pass
        def warm_up(self): pass
        def wait_until_done(self, timeout=None): return True
        def ensure_audio_loop_started(self): pass
        def stop_audio_loop(self): pass
        def audio_loop(self): pass
    
    dummy = DummyBackend()
    return "dummy", dummy


def ensure_audio_loop_started() -> None:
    _, backend = _get_backend()
    fn = getattr(backend, "ensure_audio_loop_started", None)
    if callable(fn):
        fn()


def audio_loop() -> None:
    _, backend = _get_backend()
    fn = getattr(backend, "audio_loop", None)
    if callable(fn):
        fn()


def warm_up(force: bool = False) -> None:
    name, backend = _get_backend()
    with _state_lock:
        if _warmup_done.get(name, False) and not force:
            return

    fn = getattr(backend, "warm_up", None)
    if callable(fn):
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                fn()
            except Exception as exc:
                print(f"[TTS] Warmup failed: {exc}")

    with _state_lock:
        _warmup_done[name] = True


def wait_until_done(timeout: float | None = None) -> bool:
    _, backend = _get_backend()
    fn = getattr(backend, "wait_until_done", None)
    if callable(fn):
        return bool(fn(timeout=timeout))
    return True


def stop_audio_loop() -> None:
    _, backend = _get_backend()
    fn = getattr(backend, "stop_audio_loop", None)
    if callable(fn):
        fn()


def clean_for_speech(text: str) -> str:
    if not text:
        return ""

    # Remove emojis
    text = re.sub(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U00002700-\U000027BF"
        "\U00002600-\U000026FF"
        "]+",
        "",
        text
    )

    # Remove control characters
    text = "".join(
        ch for ch in text
        if unicodedata.category(ch) != "Cf"
    )
    return text.strip()


def speak(text: str) -> None:
    """Speak text using the appropriate backend."""
    text = clean_for_speech(text)
    
    if not text:
        return

    print(f"Jarvis: {text}")

    _, backend = _get_backend()
    
    try:
        fn = getattr(backend, "speak")
        
        if _backend_name == "offline":
            # Simple synchronous speak
            fn(text)
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                fn(text)
    except Exception as exc:
        print(f"[TTS] Speak error: {exc}")


if __name__ == "__main__":
    from body.speak_TTS import initialize
    initialize()
    
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            warm_up()
        except Exception as exc:
            print(f"[TTS] Warmup failed: {exc}")
    
    speak("If internet is available, I use Edge voice.")
    speak("If internet is unavailable, I switch to offline TTS.")
    speak("Hello. Hybrid TTS is online.")
    wait_until_done(timeout=120.0)