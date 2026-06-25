"""
Jarvis TTS via Microsoft Edge neural voices (edge-tts).

Interruptible backend with generation tokens so new user commands can barge in,
stop current playback, clear queued audio, and ignore obsolete synthesis jobs.
"""

from __future__ import annotations

import asyncio
import os
import queue
import tempfile
import threading
import time
import warnings
from typing import Optional

warnings.filterwarnings("ignore")

DEFAULT_VOICE = os.environ.get("JARVIS_EDGE_VOICE", "en-GB-RyanNeural")

_audio_queue: queue.Queue[tuple[int, str] | None] = queue.Queue()
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
_pygame_ready = False


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


def _synthesize_to_mp3(text: str, path: str, voice: str) -> None:
    import edge_tts

    async def _run() -> None:
        communicate = edge_tts.Communicate(text.strip(), voice)
        await communicate.save(path)

    asyncio.run(_run())


def _ensure_pygame() -> None:
    global _pygame_ready
    if _pygame_ready:
        return
    try:
        import pygame
    except ImportError as exc:
        raise ImportError(
            "Interruptible Edge TTS playback needs pygame. Install with: pip install pygame"
        ) from exc

    with _playback_lock:
        if not _pygame_ready:
            pygame.mixer.init()
            _pygame_ready = True


def _play_mp3_interruptible(path: str, generation: int) -> None:
    _ensure_pygame()
    import pygame

    if generation != _current_generation():
        print("[TTS] Ignoring obsolete synthesis")
        return

    print("[TTS] Speaking latest response")
    _set_playing(True)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if generation != _current_generation():
                pygame.mixer.music.stop()
                print("[TTS] Playback stopped")
                break
            time.sleep(0.02)
    finally:
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        _set_playing(False)


def _discard_file(path: Optional[str]) -> None:
    if path and os.path.isfile(path):
        try:
            os.unlink(path)
        except OSError:
            pass


def _tts_worker(text: str, voice: str, my_generation: int) -> None:
    if not text or not text.strip():
        _mark_job_done()
        return

    print(f"Jarvis: {text}")
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        _synthesize_to_mp3(text, tmp_path, voice)
        if my_generation != _current_generation():
            print("[TTS] Ignoring obsolete synthesis")
            _discard_file(tmp_path)
            _mark_job_done()
            return
        _audio_queue.put((my_generation, tmp_path))
    except Exception as exc:
        print(f"[edge-tts ERROR] Failed to synthesize speech: {exc}")
        _discard_file(tmp_path)
        _mark_job_done()


def speak(text: str, voice: str | None = None) -> None:
    """Queue speech synthesis and playback without blocking the caller."""
    if not text or not text.strip():
        return
    ensure_audio_loop_started()
    text = text.replace("*", "")
    my_generation = _current_generation()
    _mark_job_started()
    threading.Thread(
        target=_tts_worker,
        args=(text, voice or DEFAULT_VOICE, my_generation),
        daemon=True,
    ).start()


def ensure_audio_loop_started() -> None:
    audio_loop()


def _audio_playback_loop() -> None:
    global _audio_loop_started, _audio_loop_thread
    while True:
        item = _audio_queue.get()
        if item is None:
            break
        generation, path = item
        try:
            if generation != _current_generation():
                print("[TTS] Ignoring obsolete synthesis")
            else:
                _play_mp3_interruptible(path, generation)
        except Exception as exc:
            print(f"[edge-tts ERROR] Failed during audio playback: {exc}")
        finally:
            _discard_file(path)
            _mark_job_done()
    with _audio_loop_lock:
        _audio_loop_started = False
        _audio_loop_thread = None


def audio_loop() -> None:
    global _audio_loop_started, _audio_loop_thread
    with _audio_loop_lock:
        if _audio_loop_started and _audio_loop_thread and _audio_loop_thread.is_alive():
            return
        _audio_loop_thread = threading.Thread(target=_audio_playback_loop, daemon=True)
        _audio_loop_thread.start()
        _audio_loop_started = True


def stop() -> None:
    """Stop current audio playback only."""
    try:
        if _pygame_ready:
            import pygame
            pygame.mixer.music.stop()
    except Exception as exc:
        print(f"[TTS] Playback stop failed: {exc}")
    print("[TTS] Playback stopped")


def cancel_all() -> None:
    """Remove every queued request and mark them completed."""
    cleared = 0
    while True:
        try:
            item = _audio_queue.get_nowait()
        except queue.Empty:
            break
        if item is None:
            _audio_queue.put(None)
            continue
        _, path = item
        _discard_file(path)
        _mark_job_done()
        cleared += 1
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


def warm_up() -> None:
    print("[edge-tts] Warming up...")
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        _synthesize_to_mp3("Ready.", tmp, DEFAULT_VOICE)
    except Exception as exc:
        print(f"[edge-tts] Warm-up skipped: {exc}")
    else:
        print("[edge-tts] Warm-up complete.")
    finally:
        _discard_file(tmp)


def stop_audio_loop() -> None:
    global _audio_loop_started
    _audio_queue.put(None)
    stop()
    with _audio_loop_lock:
        _audio_loop_started = False


def wait_until_done(timeout: float | None = None) -> bool:
    return _pending_jobs_event.wait(timeout=timeout)


if __name__ == "__main__":
    warm_up()
    speak("Hello. This is Jarvis using Edge neural text to speech.")
    wait_until_done(timeout=120.0)
