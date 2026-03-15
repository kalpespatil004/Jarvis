"""Desktop UI voice input helper with safe fallbacks."""

from __future__ import annotations

from body.listen import listen as _vosk_listen


class VoiceInputError(RuntimeError):
    """Raised when voice input cannot produce text."""


def capture_voice_text(timeout: int = 5, phrase_time_limit: int = 7) -> str:
    """Capture one utterance from the default microphone and return transcribed text.

    Uses a bundled offline listener (Vosk) provided by `body.listen`.
    """

    try:
        text = _vosk_listen()
    except Exception as exc:
        raise VoiceInputError(f"Listen error: {exc}") from exc

    text = (text or "").strip()
    if not text:
        raise VoiceInputError("No speech detected.")

    return text
