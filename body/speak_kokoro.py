"""
Offline-first TTS module using Kokoro (preferred) with pyttsx3 fallback.
Place as `body/speak.py`.

Requirements (recommended):
    pip install kokoro-onnx soundfile numpy sounddevice
or
    pip install kokoro-tts soundfile numpy sounddevice

If kokoro isn't available, falls back to pyttsx3 (install with pip install pyttsx3).
"""

import os
import sys
import tempfile
import traceback
from typing import Optional

# Playback: prefer sounddevice + soundfile for cross-platform wav playback
try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_OK = True
except Exception:
    SOUNDDEVICE_OK = False

# Primary offline TTS: try multiple kokoro wrappers (kokoro-onnx, kokoro)
KOKORO_AVAILABLE = False
KOKORO_BACKEND = None
kokoro_pipeline = None

# Try kokoro-onnx style import
try:
    # kokoro-onnx exposes a simple pipeline; exact APIs vary by package version
    # We'll try to import a pipeline function or a module that provides `pipeline(text, voice=...)`.
    import kokoro_onnx as _k_onnx  # type: ignore
    KOKORO_AVAILABLE = True
    KOKORO_BACKEND = "kokoro-onnx"
    kokoro_pipeline = getattr(_k_onnx, "pipeline", None) or getattr(_k_onnx, "infer", None)
except Exception:
    try:
        # try the kokoro-tts / kokoro CLI python bindings
        import kokoro as _k  # type: ignore
        KOKORO_AVAILABLE = True
        KOKORO_BACKEND = "kokoro"
        # many kokoro wrappers expose `pipeline(text, voice=...)`
        kokoro_pipeline = getattr(_k, "pipeline", None) or getattr(_k, "generate", None)
    except Exception:
        KOKORO_AVAILABLE = False

# Fallback offline TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False

# Helper: try to play a wav file buffer (numpy or file)
def _play_wav_file(path: str):
    if SOUNDDEVICE_OK:
        data, samplerate = sf.read(path, dtype='float32')
        sd.play(data, samplerate)
        sd.wait()
    else:
        # last resort: platform default player via os.system
        if sys.platform.startswith("win"):
            os.startfile(path)  # non-blocking
        elif sys.platform == "darwin":
            os.system(f"afplay '{path}'")
        else:
            # linux: try aplay or paplay
            if os.system(f"paplay '{path}'") != 0:
                os.system(f"aplay '{path}' &")

# Exposed voices - these are common names used in Kokoro demos; actual available voices depend on model/pack
# 'm1', 'm2' are typical male variants; 'f1' etc for female. You can enumerate voices depending on package.
DEFAULT_VOICES = {
    "m1": "male_1",
    "m2": "male_2",
    "f1": "female_1",
    "f2": "female_2",
    "af_heart": "af_heart",  # some kokoro demos use this name
}

def list_local_kokoro_voices() -> list[str]:
    """
    Try to list voices provided by the kokoro pipeline.
    Returns a best-effort list.
    """
    if not KOKORO_AVAILABLE or kokoro_pipeline is None:
        return []
    # many wrappers expose a `voices()` or `list_voices()` method
    try:
        if hasattr(kokoro_pipeline, "voices"):
            return list(kokoro_pipeline.voices())
        if hasattr(kokoro_pipeline, "list_voices"):
            return list(kokoro_pipeline.list_voices())
    except Exception:
        pass
    # fallback to DEFAULT_VOICES keys
    return list(DEFAULT_VOICES.keys())

def _kokoro_synth_to_wav(text: str, voice: str, out_path: str) -> bool:
    """
    Use the kokoro pipeline to synthesize text into a wav file at out_path.
    Returns True on success, False otherwise.
    """
    try:
        if not KOKORO_AVAILABLE or kokoro_pipeline is None:
            return False

        # Different kokoro wrappers expose slightly different APIs.
        # We attempt multiple reasonable signatures.
        # 1) pipeline(text, voice=voice) -> yields (meta, params, audio) or returns audio numpy
        # 2) pipeline.generate(text, voice=voice) -> returns bytes / array
        # 3) direct function call kokoro_pipeline(text, voice=voice)

        pipeline = kokoro_pipeline

        # Try calling as generator-style pipeline
        try:
            # some pipelines return a generator that yields (gs, ps, audio_bytes)
            result = pipeline(text, voice=voice)
            # If result is generator/iterator
            if hasattr(result, "__iter__") and not isinstance(result, (bytes, bytearray)):
                # consume generator and pick first audio-like output
                for item in result:
                    # item might be tuple (gs, ps, audio) or audio directly
                    if isinstance(item, (bytes, bytearray)):
                        audio_bytes = bytes(item)
                        with open(out_path, "wb") as f:
                            f.write(audio_bytes)
                        return True
                    if isinstance(item, (list, tuple)) and len(item) >= 3:
                        audio = item[2]
                        # audio may be numpy array or bytes
                        if hasattr(audio, "dtype"):
                            # numpy array -> write with soundfile
                            sf.write(out_path, audio, 24000)  # sample rate best-effort
                            return True
                        elif isinstance(audio, (bytes, bytearray)):
                            with open(out_path, "wb") as f:
                                f.write(audio)
                            return True
                # if generator didn't produce usable output
            # If result is bytes
            if isinstance(result, (bytes, bytearray)):
                with open(out_path, "wb") as f:
                    f.write(result)
                return True
            # If result is numpy array
            if hasattr(result, "dtype"):
                sf.write(out_path, result, 24000)
                return True

        except TypeError:
            # pipeline requires kwargs like pipeline(text=text, voice=voice)
            try:
                result = pipeline(text=text, voice=voice)
                if isinstance(result, (bytes, bytearray)):
                    with open(out_path, "wb") as f:
                        f.write(result)
                    return True
                if hasattr(result, "__iter__"):
                    for item in result:
                        if isinstance(item, (bytes, bytearray)):
                            with open(out_path, "wb") as f:
                                f.write(item)
                            return True
                        if isinstance(item, (list, tuple)) and len(item) >= 3:
                            audio = item[2]
                            if hasattr(audio, "dtype"):
                                sf.write(out_path, audio, 24000)
                                return True
                            elif isinstance(audio, (bytes, bytearray)):
                                with open(out_path, "wb") as f:
                                    f.write(audio)
                                return True
            except Exception:
                pass

        # Last-resort: try pipeline.generate / pipeline.infer
        for alt in ("generate", "infer", "synthesize"):
            if hasattr(pipeline, alt):
                try:
                    fn = getattr(pipeline, alt)
                    result = fn(text, voice=voice)
                    if isinstance(result, (bytes, bytearray)):
                        with open(out_path, "wb") as f:
                            f.write(result)
                        return True
                    if hasattr(result, "dtype"):
                        sf.write(out_path, result, 24000)
                        return True
                except Exception:
                    continue

        # If we reach here, we couldn't synthesize
        return False

    except Exception:
        traceback.print_exc()
        return False

def speak(text: str,
          voice: str = "m1",
          use_kokoro: Optional[bool] = True,
          verbose: bool = True) -> None:
    """
    Speak text out loud.
    Args:
        text: text to speak
        voice: voice id/name (e.g., 'm1', 'm2', 'f1', or specific kokoro voice names)
        use_kokoro: if True, try kokoro first (offline). If False, skip kokoro.
        verbose: print the text before speaking
    """
    if not text or not text.strip():
        return

    if verbose:
        print(f"Jarvis: {text}")

    # Normalize voice
    effective_voice = voice or "m1"
    # Map shortcuts to kokoro voice names, if necessary
    effective_voice_name = DEFAULT_VOICES.get(effective_voice, effective_voice)

    # Try Kokoro offline synthesis
    if use_kokoro and KOKORO_AVAILABLE:
        tmp_wav = os.path.join(tempfile.gettempdir(), f"jarvis_kokoro_{abs(hash(text)) % 100000}.wav")
        ok = _kokoro_synth_to_wav(text, effective_voice_name, tmp_wav)
        if ok and os.path.exists(tmp_wav):
            try:
                _play_wav_file(tmp_wav)
                # optionally delete temp file
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass
                return
            except Exception:
                # playback failed; fall back
                pass

    # Fallback to pyttsx3 offline TTS
    if PYTTSX3_AVAILABLE:
        try:
            engine = pyttsx3.init()
            # try to pick a male-ish voice if available and voice is m1/m2
            voices = engine.getProperty('voices')
            # simple heuristic: pick first voice whose name contains 'male' or pick by index
            chosen_id = None
            if effective_voice.startswith("m"):
                # try to use index 0 or 1
                try:
                    idx = int(effective_voice[1:]) - 1
                    if 0 <= idx < len(voices):
                        chosen_id = voices[idx].id
                except Exception:
                    chosen_id = None
            if chosen_id is None:
                # fallback: try to find 'male' in voice name
                for v in voices:
                    if 'male' in v.name.lower() or 'male' in (v.id or '').lower():
                        chosen_id = v.id
                        break
            if chosen_id:
                engine.setProperty('voice', chosen_id)
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            return
        except Exception:
            traceback.print_exc()

    # Last resort: raise an error
    raise RuntimeError("No TTS engine available. Install kokoro-onnx or kokoro-tts, or pyttsx3.")

# Utility for testing
if __name__ == "__main__":
    print("KOKORO_AVAILABLE:", KOKORO_AVAILABLE, "BACKEND:", KOKORO_BACKEND)
    print("PYTTSX3_AVAILABLE:", PYTTSX3_AVAILABLE)
    print("SOUNDDEVICE_OK:", SOUNDDEVICE_OK)
    print("Available kokoro voices (best-effort):", list_local_kokoro_voices())
    # quick test
    speak("Hello. This is your offline Jarvis.", voice="m1", verbose=True)
