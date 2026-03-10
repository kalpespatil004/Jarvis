"""Desktop UI voice input helper with safe fallbacks."""

from __future__ import annotations

try:
    import speech_recognition as sr
except Exception:  # dependency not installed
    sr = None


class VoiceInputError(RuntimeError):
    """Raised when voice input cannot produce text."""


def capture_voice_text(timeout: int = 5, phrase_time_limit: int = 7) -> str:
    """
    Capture one utterance from the default microphone and return transcribed text.

    Uses SpeechRecognition with Google Web Speech API for simple setup.
    """
    if sr is None:
        raise VoiceInputError(
            "speech_recognition is not installed. Run: pip install SpeechRecognition pyaudio"
        )

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
    except Exception as exc:  # microphone/device/runtime issues
        raise VoiceInputError(f"Microphone error: {exc}") from exc

    try:
        text = recognizer.recognize_google(audio)
    except sr.UnknownValueError as exc:
        raise VoiceInputError("I could not understand your voice.") from exc
    except sr.RequestError as exc:
        raise VoiceInputError(
            "Speech recognition service is unavailable. Check internet connection."
        ) from exc

    text = text.strip()
    if not text:
        raise VoiceInputError("No speech detected.")

    return text
