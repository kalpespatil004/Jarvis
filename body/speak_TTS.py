"""Interruptible offline Jarvis TTS using Coqui."""

from __future__ import annotations

import queue
import threading
import warnings

warnings.filterwarnings("ignore")

import sounddevice as sd
import torch
from TTS.api import TTS

MODEL_NAME = "tts_models/en/vctk/vits"
SAMPLE_RATE = 22050
USE_GPU = torch.cuda.is_available()
DEFAULT_SPEAKER = "p230"

print("[TTS] Initializing voice engine...")
_tts = TTS(MODEL_NAME, gpu=USE_GPU)

_audio_queue: queue.Queue[tuple[int, list[float]] | None] = queue.Queue()
_audio_loop_started = False
_audio_loop_lock = threading.Lock()
_audio_loop_thread: threading.Thread | None = None

_pending_jobs = 0
_pending_jobs_lock = threading.Lock()
_pending_jobs_event = threading.Event()
_pending_jobs_event.set()

_generation = 0
_generation_lock = threading.Lock()
_playback_lock = threading.Lock()
_is_playing = False


def _current_generation() -> int:
    with _generation_lock:
        return _generation


def _bump_generation() -> int:
    global _generation
    with _generation_lock:
        _generation += 1
        return _generation


def _mark_job_started() -> None:
    global _pending_jobs
    with _pending_jobs_lock:
        _pending_jobs += 1
        _pending_jobs_event.clear()


def _mark_job_done() -> None:
    global _pending_jobs
    with _pending_jobs_lock:
        _pending_jobs = max(0, _pending_jobs - 1)
        if _pending_jobs == 0:
            _pending_jobs_event.set()


def _set_playing(value: bool) -> None:
    global _is_playing
    with _playback_lock:
        _is_playing = value


def _tts_worker(text: str, my_generation: int) -> None:
    if not text or not text.strip():
        _mark_job_done()
        return

    print(f"Jarvis: {text}")
    try:
        wav = _tts.tts(text=text, speaker=DEFAULT_SPEAKER)
        if my_generation != _current_generation():
            print("[TTS] Ignoring obsolete synthesis")
            _mark_job_done()
            return
        _audio_queue.put((my_generation, wav))
    except Exception as exc:
        print(f"[TTS ERROR] Failed to synthesize speech: {exc}")
        _mark_job_done()


def speak(text: str) -> None:
    if not text or not text.strip():
        return
    ensure_audio_loop_started()
    text = text.replace("*", "")
    my_generation = _current_generation()
    _mark_job_started()
    threading.Thread(target=_tts_worker, args=(text, my_generation), daemon=True).start()


def ensure_audio_loop_started() -> None:
    global _audio_loop_started, _audio_loop_thread
    with _audio_loop_lock:
        if _audio_loop_started and _audio_loop_thread and _audio_loop_thread.is_alive():
            return
        _audio_loop_thread = threading.Thread(target=audio_loop, daemon=True)
        _audio_loop_thread.start()
        _audio_loop_started = True


def audio_loop() -> None:
    global _audio_loop_started, _audio_loop_thread
    while True:
        item = _audio_queue.get()
        if item is None:
            break
        generation, wav = item
        try:
            if generation != _current_generation():
                print("[TTS] Ignoring obsolete synthesis")
            else:
                print("[TTS] Speaking latest response")
                _set_playing(True)
                sd.play(wav, SAMPLE_RATE)
                sd.wait()
        except Exception as exc:
            print(f"[TTS ERROR] Failed during audio playback: {exc}")
        finally:
            _set_playing(False)
            _mark_job_done()
    with _audio_loop_lock:
        _audio_loop_started = False
        _audio_loop_thread = None


def stop() -> None:
    """Stop current audio playback only."""
    try:
        sd.stop()
    except Exception as exc:
        print(f"[TTS] Playback stop failed: {exc}")
    print("[TTS] Playback stopped")


def cancel_all() -> None:
    """Remove every queued request and mark them completed."""
    while True:
        try:
            item = _audio_queue.get_nowait()
        except queue.Empty:
            break
        if item is None:
            _audio_queue.put(None)
            continue
        _mark_job_done()
    print("[TTS] Queue cleared")


def interrupt() -> None:
    """Stop playback, clear queued audio, and invalidate pending synthesis."""
    print("[TTS] Interrupt requested")
    generation = _bump_generation()
    stop()
    cancel_all()
    print(f"[TTS] Generation -> {generation}")


def is_speaking() -> bool:
    with _playback_lock:
        return _is_playing or not _audio_queue.empty()


def wait_until_done(timeout: float | None = None) -> bool:
    return _pending_jobs_event.wait(timeout=timeout)


def warm_up() -> None:
    print("[TTS] Warming up...")
    _tts.tts("System online.", speaker=DEFAULT_SPEAKER)  # type: ignore
    print("[TTS] Warm-up complete.")


def stop_audio_loop() -> None:
    global _audio_loop_started
    _audio_queue.put(None)
    stop()
    with _audio_loop_lock:
        _audio_loop_started = False


if __name__ == "__main__":
    print("[TTS] Running standalone test")
    warm_up()
    speak("Hello. This is Jarvis. Text to speech is online.")
    wait_until_done(timeout=120.0)
