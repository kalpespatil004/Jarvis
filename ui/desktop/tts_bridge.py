"""Safe bridge for desktop UI speech output.

Keeps UI usable even if heavy TTS dependencies are missing or fail at runtime.
"""

from __future__ import annotations

from typing import Optional


def speak_text(text: str) -> Optional[str]:
    """Try speaking text via body.speak and return an error message on failure."""
    if not text or not text.strip():
        return None

    try:
        # Lazy import so desktop UI can still open if TTS stack is unavailable.
        from body.speak import speak

        speak(text)
        return None
    except Exception as exc:
        return f"Voice output failed: {exc}"
