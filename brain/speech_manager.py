from __future__ import annotations

from body import speak as tts


def speak(text: str) -> None:
    tts.speak(text)


def interrupt() -> None:
    tts.interrupt()


def stop() -> None:
    tts.stop()


def cancel_all() -> None:
    tts.cancel_all()


def is_speaking() -> bool:
    return tts.is_speaking()


def wait_until_done(timeout: float | None = None) -> bool:
    return tts.wait_until_done(timeout=timeout)


def warm_up(force: bool = False) -> None:
    tts.warm_up(force=force)


def ensure_audio_loop_started() -> None:
    tts.ensure_audio_loop_started()
