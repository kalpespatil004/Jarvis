"""Safe bridge for desktop UI speech output.

Keeps UI usable even if heavy TTS dependencies are missing or fail at runtime.

Set ``JARVIS_USE_EDGE_TTS=1`` to use ``body.speak_edgetts`` (edge-tts) instead of
``body.speak`` (local Coqui TTS). Edge voices need network access.
"""

from __future__ import annotations

import os
from typing import Optional


def _use_edge_tts() -> bool:
    return os.environ.get("JARVIS_USE_EDGE_TTS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "edge",
    )


def speak_text(text: str) -> Optional[str]:
    """Try speaking text via body.speak (or edge-tts when enabled) and return an error message on failure."""
    if not text or not text.strip():
        return None

    try:
        # Lazy import so desktop UI can still open if TTS stack is unavailable.
        if _use_edge_tts():
            from body.speak_edgetts import speak
        else:
            from body.speak import speak

        speak(text)
        return None
    except Exception as exc:
        return f"Voice output failed: {exc}"
