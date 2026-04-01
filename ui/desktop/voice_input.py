"""Desktop voice helpers: Vosk wake-word detection plus isolated Whisper command capture."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from body.listen_vosk import WAKE_PHRASES, listen_for_wake_word as vosk_listen_for_wake_word

WHISPER_RESULT_PREFIX = "__WHISPER_RESULT__"
WHISPER_ERROR_PREFIX = "__WHISPER_ERROR__"


class VoiceInputError(RuntimeError):
    """Raised when desktop voice input cannot produce text."""


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def strip_wake_prefix(text: str) -> str:
    normalized = normalize_text(text)
    for wake_phrase in sorted(WAKE_PHRASES, key=len, reverse=True):
        prefix = normalize_text(wake_phrase)
        if normalized == prefix:
            return ""
        if normalized.startswith(prefix + " "):
            return normalized[len(prefix):].strip()
    return normalized


def extract_inline_command(text: str) -> str:
    return strip_wake_prefix(text)


def listen_for_wake_word(stop_event=None) -> str:
    text = vosk_listen_for_wake_word(stop_event=stop_event)
    return normalize_text(text)


def capture_command_text() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "ui.desktop.whisper_runner"]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise VoiceInputError("Whisper command capture timed out.") from exc
    except Exception as exc:
        raise VoiceInputError(f"Unable to start Whisper command capture: {exc}") from exc

    output_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    error_lines = [line.strip() for line in completed.stderr.splitlines() if line.strip()]

    for line in reversed(output_lines):
        if line.startswith(WHISPER_RESULT_PREFIX):
            text = strip_wake_prefix(line[len(WHISPER_RESULT_PREFIX):])
            if not text:
                raise VoiceInputError("Please say your command after the wake word.")
            return text

    details = []
    for line in error_lines + output_lines:
        if line.startswith(WHISPER_ERROR_PREFIX):
            details.append(line[len(WHISPER_ERROR_PREFIX):].strip())
        elif line:
            details.append(line)

    message = details[-1] if details else f"Whisper exited with code {completed.returncode}."
    raise VoiceInputError(message)


def capture_voice_text() -> str:
    return capture_command_text()
