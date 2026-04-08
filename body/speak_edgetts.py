"""
Jarvis TTS via Microsoft Edge neural voices (edge-tts).

Mirrors ``body.speak`` so it is drop-in for the desktop UI and ``tts_bridge``:
``speak``, ``ensure_audio_loop_started``, ``audio_loop``, ``warm_up``.

Requires network for synthesis. Install::

    pip install edge-tts "playsound==1.2.2"
"""

from __future__ import annotations

import asyncio
import os
import queue
import tempfile
import threading
import warnings
import time
warnings.filterwarnings("ignore")

# Male English neural voice (change via env JARVIS_EDGE_VOICE if you prefer another).
DEFAULT_VOICE = os.environ.get("JARVIS_EDGE_VOICE", "en-AU-WilliamNeural")

_audio_queue: queue.Queue[str | None] = queue.Queue()
_audio_loop_started = False
_audio_loop_lock = threading.Lock()
_audio_loop_thread: threading.Thread | None = None
_pending_jobs = 0
_pending_jobs_lock = threading.Lock()
_pending_jobs_event = threading.Event()
_pending_jobs_event.set()


def _synthesize_to_mp3(text: str, path: str, voice: str) -> None:
    import edge_tts

    async def _run() -> None:
        communicate = edge_tts.Communicate(text.strip(), voice)
        await communicate.save(path)

    asyncio.run(_run())


def _play_mp3(path: str) -> None:
    try:
        from playsound import playsound
    except ImportError as exc:
        raise ImportError(
            "Playback needs playsound. Install with: pip install playsound"
        ) from exc
    playsound(path, block=True)


def _tts_worker(text: str, voice: str) -> None:
    if not text or not text.strip():
        return

    print(f"Jarvis: {text}")
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        _synthesize_to_mp3(text, tmp_path, voice)
        _audio_queue.put(tmp_path)
    except Exception as exc:
        print(f"[edge-tts ERROR] Failed to synthesize speech: {exc}")
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        _mark_job_done()


def speak(text: str, voice: str | None = None) -> None:
    """Queue speech synthesis and playback without blocking the caller (e.g. Qt UI thread)."""
    ensure_audio_loop_started()
    text = text.replace("*", "")
    _mark_job_started()
    threading.Thread(
        target=_tts_worker,
        args=(text, voice or DEFAULT_VOICE),
        daemon=True,
    ).start()


def ensure_audio_loop_started() -> None:
    """Start the playback loop once in a background thread (needed for UI mode)."""
    audio_loop()


def _audio_playback_loop() -> None:
    """Internal worker: drains synthesized audio files and plays them sequentially."""
    global _audio_loop_started, _audio_loop_thread
    while True:
        path = _audio_queue.get()
        if path is None:
            break
        try:
            _play_mp3(path)
        except Exception as exc:
            print(f"[edge-tts ERROR] Failed during audio playback: {exc}")
        finally:
            try:
                if os.path.isfile(path):
                    os.unlink(path)
            except OSError:
                pass
            _mark_job_done()
    with _audio_loop_lock:
        _audio_loop_started = False
        _audio_loop_thread = None


def audio_loop() -> None:
    """
    Ensure playback worker is running in the background and return immediately.

    This keeps compatibility with callers that invoke `audio_loop()` directly while
    guaranteeing the rest of the program keeps running.
    """
    global _audio_loop_started, _audio_loop_thread
    with _audio_loop_lock:
        if _audio_loop_started and _audio_loop_thread and _audio_loop_thread.is_alive():
            return
        _audio_loop_thread = threading.Thread(target=_audio_playback_loop, daemon=True)
        _audio_loop_thread.start()
        _audio_loop_started = True


def warm_up() -> None:
    """Prime DNS / first request so the first user utterance is snappier."""
    print("[edge-tts] Warming up...")
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        _synthesize_to_mp3("Ready.", tmp, DEFAULT_VOICE)
        if os.path.isfile(tmp):
            os.unlink(tmp)
    except Exception as exc:
        print(f"[edge-tts] Warm-up skipped: {exc}")
    else:
        print("[edge-tts] Warm-up complete.")


def stop_audio_loop() -> None:
    """Optional: stop ``audio_loop`` (mostly for tests)."""
    global _audio_loop_started
    _audio_queue.put(None)
    with _audio_loop_lock:
        _audio_loop_started = False


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


def wait_until_done(timeout: float | None = None) -> bool:
    """
    Block until all queued speech is synthesized and played.

    Returns True when queue is fully drained; False on timeout.
    """
    return _pending_jobs_event.wait(timeout=timeout)


if __name__ == "__main__":

    warm_up()
    text1= "Hello. This is Jarvis using Edge neural text to speech."
    text2= "Hello. This is Jarvis what are you doing?"
    text= "Hello. i am Jarvis, how can i help you today?"
    
    speak(text )
    speak(text1 )
    speak(text2 )
    
    wait_until_done(timeout=120.0)