"""
Hybrid TTS router for Jarvis.

- Online: use ``body.speak_edgetts`` (edge-tts backend)
- Offline: use ``body.speak_TTS`` (local Coqui backend)

Public API mirrors both backends: ``speak``, ``ensure_audio_loop_started``,
``audio_loop``, ``warm_up``, ``interrupt``, ``stop``, ``cancel_all``,
``is_speaking``.
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




# Repo root must be on path so ``body.speak_TTS`` / ``body.speak_edgetts`` always
# resolve to this project (not a third-party ``speak_TTS`` on sys.path).
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_state_lock = threading.Lock()
_backend_name: Optional[str] = None
_backend_module: Optional[ModuleType] = None
_warmup_done = {"edge": False, "offline": False}

_connectivity_cache_ttl_s = 3.0
_last_connectivity_check = 0.0
_last_connectivity_result = False


def _internet_available(timeout_s: float = 0.8) -> bool:
    """Quick internet check with short-lived cache."""
    global _last_connectivity_check, _last_connectivity_result
    now = time.monotonic()
    if now - _last_connectivity_check < _connectivity_cache_ttl_s:
        return _last_connectivity_result

    ok = False
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=timeout_s):
            ok = True
    except OSError:
        ok = False

    _last_connectivity_check = now
    _last_connectivity_result = ok
    return ok


def _import_backend(name: str) -> ModuleType:
    if name == "edge":
        return importlib.import_module("body.speak_edgetts")
    return importlib.import_module("body.speak_TTS")


def _get_backend() -> tuple[str, ModuleType]:
    """
    Choose backend dynamically.
    - online -> edge
    - offline -> local TTS
    Falls back to local TTS if edge backend import fails.
    """
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
                print(f"[TTS] Edge backend unavailable, falling back offline: {exc}")
                module = _import_backend("offline")
                chosen = "offline"
            else:
                raise

        if chosen != _backend_name:
            print(f"[TTS] Using backend: {chosen}")

        _backend_name = chosen
        _backend_module = module
        return chosen, module



def _loaded_backends() -> list[ModuleType]:
    """Return TTS backends that are already loaded without importing heavy deps."""
    modules: list[ModuleType] = []
    with _state_lock:
        if _backend_module is not None:
            modules.append(_backend_module)
    for module_name in ("body.speak_edgetts", "body.speak_TTS"):
        module = sys.modules.get(module_name)
        if module is not None and module not in modules:
            modules.append(module)
    return modules


def _call_loaded_backends(function_name: str) -> bool:
    """Call a lifecycle function on loaded backends; return True if any ran."""
    called = False
    for backend in _loaded_backends():
        fn = getattr(backend, function_name, None)
        if callable(fn):
            fn()
            called = True
    return called

def ensure_audio_loop_started() -> None:
    _, backend = _get_backend()
    fn = getattr(backend, "ensure_audio_loop_started", None)
    if callable(fn):
        fn()


def audio_loop() -> None:
    """
    Keep compatibility with existing callers.
    Delegates to active backend implementation.
    """
    _, backend = _get_backend()
    fn = getattr(backend, "audio_loop", None)
    if callable(fn):
        fn()



def warm_up(force: bool = False) -> None:
    """
    Warm up current backend once (unless force=True).
    This avoids warming up on every function call.
    """
    name, backend = _get_backend()
    with _state_lock:
        if _warmup_done.get(name, False) and not force:
            return

    fn = getattr(backend, "warm_up", None)
    if callable(fn):
        fn()

    with _state_lock:
        _warmup_done[name] = True


def wait_until_done(timeout: float | None = None) -> bool:
    """
    Wait for current backend queue to finish speaking.
    Returns True when completed, False on timeout.
    """
    _, backend = _get_backend()
    fn = getattr(backend, "wait_until_done", None)
    if callable(fn):
        return bool(fn(timeout=timeout))
    return True



def interrupt() -> None:
    """Stop playback, clear queued speech, and invalidate pending synthesis."""
    if not _call_loaded_backends("interrupt"):
        _, backend = _get_backend()
        fn = getattr(backend, "interrupt", None)
        if callable(fn):
            fn()


def stop() -> None:
    """Stop current audio playback only."""
    if not _call_loaded_backends("stop"):
        _, backend = _get_backend()
        fn = getattr(backend, "stop", None)
        if callable(fn):
            fn()


def cancel_all() -> None:
    """Clear queued speech without stopping current playback."""
    if not _call_loaded_backends("cancel_all"):
        _, backend = _get_backend()
        fn = getattr(backend, "cancel_all", None)
        if callable(fn):
            fn()


def is_speaking() -> bool:
    """Return True when any loaded backend is synthesizing or playing audio."""
    checked = False
    for backend in _loaded_backends():
        fn = getattr(backend, "is_speaking", None)
        if callable(fn):
            checked = True
            if bool(fn()):
                return True
    if checked:
        return False
    _, backend = _get_backend()
    fn = getattr(backend, "is_speaking", None)
    return bool(fn()) if callable(fn) else False

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

    text = "".join(
        ch for ch in text
        if unicodedata.category(ch) != "Cf"
    )
    return text.strip()

def speak(text: str):
    print("BEFORE:", repr(text))

    text = clean_for_speech(text)

    print("AFTER :", repr(text))

    
    if not text:
        return

    print(f"[TTS] {text}")  # Debug

    _, backend = _get_backend()

    fn = getattr(backend, "speak")
    fn(text)

if __name__ == "__main__":
    warm_up()
    speak("If internet is available, I use Edge voice.")
    speak("If internet is unavailable, I switch to offline TTS.")
    speak("Hello. Hybrid TTS is online🤣😘🤷💕.")
    wait_until_done(timeout=120.0)
