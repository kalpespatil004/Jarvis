"""
Hybrid TTS router for Jarvis.

- Online: use ``body.speak_edgetts`` (edge-tts backend)
- Offline: use ``body.speak_TTS`` (local Coqui backend)

Public API mirrors both backends: ``speak``, ``ensure_audio_loop_started``,
``audio_loop``, ``warm_up``.
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


def speak(text: str) -> None:
    _, backend = _get_backend()
    fn = getattr(backend, "speak")
    fn(text)


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


def stop_audio_loop() -> None:
    _, backend = _get_backend()
    fn = getattr(backend, "stop_audio_loop", None)
    if callable(fn):
        fn()


if __name__ == "__main__":
    warm_up()
    speak("Hello. Hybrid TTS is online.")
    speak("If internet is available, I use Edge voice.")
    speak("If internet is unavailable, I switch to offline TTS.")
    wait_until_done(timeout=120.0)
