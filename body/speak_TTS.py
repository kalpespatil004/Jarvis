# """
# Jarvis TTS – Production Offline Engine (CPU-only)
# ------------------------------------------------
# - Forces CPU mode to avoid CUDA/cuDNN crashes
# - Singleton TTSManager with dedicated worker threads
# - Fast, non-blocking synthesis
# - Minimal console output
# """

# import warnings
# warnings.filterwarnings("ignore")

# import os
# import sys
# import queue
# import threading
# import time
# import logging
# from typing import Optional

# # Force CPU mode
# os.environ["CUDA_VISIBLE_DEVICES"] = ""
# os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
# os.environ["TTS_LOGGING"] = "ERROR"
# os.environ["COQUI_LOGGING"] = "ERROR"

# import sounddevice as sd
# import torch
# from TTS.api import TTS

# # Suppress ALL logs
# logging.getLogger("TTS").setLevel(logging.ERROR)
# logging.getLogger("coqui").setLevel(logging.ERROR)
# logging.getLogger("torch").setLevel(logging.ERROR)
# logging.getLogger("sounddevice").setLevel(logging.ERROR)

# # ===============================
# # CONFIGURATION
# # ===============================

# MODEL_NAME = "tts_models/en/vctk/vits"
# SAMPLE_RATE = 22050
# DEFAULT_SPEAKER = "p230"
# QUEUE_TIMEOUT = 0.1


# # ===============================
# # CONTEXT MANAGER FOR SUPPRESSING OUTPUT
# # ===============================

# class SuppressOutput:
#     def __enter__(self):
#         self._stdout = sys.stdout
#         self._stderr = sys.stderr
#         sys.stdout = open(os.devnull, 'w')
#         sys.stderr = open(os.devnull, 'w')
#         return self
    
#     def __exit__(self, *args):
#         sys.stdout.close()
#         sys.stderr.close()
#         sys.stdout = self._stdout
#         sys.stderr = self._stderr


# # ===============================
# # SINGLETON MANAGER
# # ===============================

# class TTSManager:
#     """Thread-safe singleton manager for offline TTS."""

#     def __init__(self):
#         self._lock = threading.Lock()
#         self._load_lock = threading.Lock()
#         self._started = False
#         self._shutdown_event = threading.Event()
#         self._stop_requested = False
#         self._model_loaded = False
#         self._model_failed = False
#         self._initialized = False

#         # Queues
#         self._text_queue: queue.Queue = queue.Queue()
#         self._audio_queue: queue.Queue = queue.Queue()

#         # Threads
#         self._synth_thread: Optional[threading.Thread] = None
#         self._playback_thread: Optional[threading.Thread] = None

#         # Model
#         self._model: Optional[TTS] = None

#         # Pending jobs
#         self._pending_count = 0
#         self._pending_lock = threading.Lock()
#         self._pending_event = threading.Event()
#         self._pending_event.set()

#         # Audio state
#         self._is_playing = False

#     def _load_model(self) -> bool:
#         """Load Coqui TTS model on CPU only."""
#         with self._load_lock:
#             if self._model_loaded:
#                 return True
#             if self._model_failed:
#                 return False

#             try:
#                 print("[TTS] Loading model on CPU...")
#                 with SuppressOutput():
#                     model = TTS(MODEL_NAME, gpu=False)
#                 self._model = model
#                 self._model_loaded = True
#                 print("[TTS] Model loaded on CPU")
#                 return True
#             except Exception as exc:
#                 print(f"[TTS] Failed to load model: {exc}")
#                 self._model_failed = True
#                 return False

#     def _start_workers(self) -> None:
#         """Start synthesis and playback threads."""
#         with self._lock:
#             if self._started or self._shutdown_event.is_set():
#                 return
#             self._started = True

#         self._synth_thread = threading.Thread(
#             target=self._synthesis_worker,
#             daemon=True,
#             name="TTSSynthWorker"
#         )
#         self._playback_thread = threading.Thread(
#             target=self._playback_worker,
#             daemon=True,
#             name="TTSPlaybackWorker"
#         )
#         self._synth_thread.start()
#         self._playback_thread.start()

#     def _increment_pending(self) -> None:
#         with self._pending_lock:
#             self._pending_count += 1
#             self._pending_event.clear()

#     def _decrement_pending(self) -> None:
#         with self._pending_lock:
#             self._pending_count -= 1
#             if self._pending_count <= 0:
#                 self._pending_count = 0
#                 self._pending_event.set()

#     def _drain_queue_and_decrement(self, q: queue.Queue) -> None:
#         count = 0
#         while True:
#             try:
#                 q.get_nowait()
#                 count += 1
#             except queue.Empty:
#                 break
#         for _ in range(count):
#             self._decrement_pending()

#     def _synthesis_worker(self) -> None:
#         """Continuously synthesize text to audio."""
#         if not self._model_loaded:
#             print("[TTS] ERROR: Model not loaded. Synthesis worker stopping.")
#             return

#         while not self._shutdown_event.is_set():
#             try:
#                 text = self._text_queue.get(timeout=QUEUE_TIMEOUT)
#             except queue.Empty:
#                 continue

#             if self._stop_requested:
#                 self._decrement_pending()
#                 continue

#             try:
#                 # Suppress ALL output during synthesis
#                 with SuppressOutput():
#                     wav = self._model.tts(text, speaker=DEFAULT_SPEAKER)
#                 self._audio_queue.put(wav)
#             except Exception as exc:
#                 print(f"[TTS ERROR] Synthesis failed: {exc}")
#                 self._decrement_pending()

#     def _playback_worker(self) -> None:
#         """Continuously play audio."""
#         while not self._shutdown_event.is_set():
#             try:
#                 wav = self._audio_queue.get(timeout=QUEUE_TIMEOUT)
#             except queue.Empty:
#                 continue

#             if self._stop_requested:
#                 self._decrement_pending()
#                 continue

#             try:
#                 self._is_playing = True
#                 sd.play(wav, SAMPLE_RATE)
#                 sd.wait()
#             except Exception as exc:
#                 print(f"[TTS ERROR] Playback failed: {exc}")
#             finally:
#                 self._is_playing = False
#                 self._decrement_pending()

#     # ---------- Public API ----------

#     def initialize(self) -> bool:
#         """Initialize the TTS engine."""
#         if self._initialized:
#             return True
            
#         print("[TTS] Initializing offline TTS engine...")
        
#         if not self._load_model():
#             print("[TTS] Failed to initialize offline TTS")
#             return False
        
#         self._start_workers()
        
#         print("[TTS] Warming up...")
#         try:
#             with SuppressOutput():
#                 self._model.tts("System online.", speaker=DEFAULT_SPEAKER)
#             print("[TTS] Warmup complete")
#         except Exception as exc:
#             print(f"[TTS] Warmup failed: {exc}")
#             return False
        
#         self._initialized = True
#         print("[TTS] Offline TTS engine ready")
#         return True

#     def warm_up(self) -> None:
#         """Prime model."""
#         if not self._initialized:
#             self.initialize()
#             return
            
#         if not self._model_loaded:
#             if not self._load_model():
#                 print("[TTS] WARNING: Model not available. Warmup skipped.")
#                 return
            
#         self._start_workers()
#         print("[TTS] Warming up...")
#         try:
#             with SuppressOutput():
#                 self._model.tts("System online.", speaker=DEFAULT_SPEAKER)
#             print("[TTS] Warmup complete")
#         except Exception as exc:
#             print(f"[TTS] Warmup failed: {exc}")

#     def speak(self, text: str) -> None:
#         """Queue text for speech (non-blocking)."""
#         if not text or not text.strip():
#             return

#         if not self._model_loaded:
#             if not self._load_model():
#                 print("[TTS] ERROR: Model not available. Cannot speak.")
#                 return

#         self._start_workers()
#         self._increment_pending()
#         self._text_queue.put(text.strip())

#     def stop(self) -> None:
#         """Interrupt current speech."""
#         self._stop_requested = True
#         self._drain_queue_and_decrement(self._text_queue)
#         self._drain_queue_and_decrement(self._audio_queue)
#         if self._is_playing:
#             try:
#                 sd.stop()
#             except Exception:
#                 pass
#         self._stop_requested = False

#     def shutdown(self) -> None:
#         """Clean shutdown."""
#         self._shutdown_event.set()
#         try:
#             sd.stop()
#         except Exception:
#             pass
#         if self._synth_thread and self._synth_thread.is_alive():
#             self._synth_thread.join(timeout=1.0)
#         if self._playback_thread and self._playback_thread.is_alive():
#             self._playback_thread.join(timeout=1.0)
#         with self._lock:
#             self._started = False
#         self._text_queue.queue.clear()
#         self._audio_queue.queue.clear()
#         self._model = None
#         self._model_loaded = False
#         self._initialized = False
#         print("[TTS] Shutdown complete")

#     def wait_until_done(self, timeout: Optional[float] = None) -> bool:
#         """Wait for all speech to finish."""
#         start_time = time.time()
#         while not self._text_queue.empty() or not self._audio_queue.empty():
#             if timeout is not None:
#                 elapsed = time.time() - start_time
#                 if elapsed >= timeout:
#                     return False
#             time.sleep(0.05)
        
#         if timeout is not None:
#             elapsed = time.time() - start_time
#             remaining = timeout - elapsed
#             if remaining <= 0:
#                 return False
#             return self._pending_event.wait(timeout=remaining)
#         else:
#             return self._pending_event.wait()

#     def ensure_audio_loop_started(self) -> None:
#         """Start workers if not running."""
#         if not self._model_loaded:
#             self._load_model()
#         self._start_workers()


# # ===============================
# # SINGLETON INSTANCE
# # ===============================

# _manager = TTSManager()


# # ===============================
# # PUBLIC FUNCTIONS
# # ===============================

# def speak(text: str) -> None:
#     _manager.speak(text)


# def stop() -> None:
#     _manager.stop()


# def warm_up() -> None:
#     _manager.warm_up()


# def shutdown() -> None:
#     _manager.shutdown()


# def wait_until_done(timeout: Optional[float] = None) -> bool:
#     return _manager.wait_until_done(timeout)


# def ensure_audio_loop_started() -> None:
#     _manager.ensure_audio_loop_started()


# def initialize() -> bool:
#     return _manager.initialize()


# # ===============================
# # STANDALONE TEST
# # ===============================

# if __name__ == "__main__":
#     print("[TEST] Starting offline TTS test (CPU mode)")
#     initialize()

#     speak("Hello. This is Jarvis. Text to speech is online.")
#     speak("I can speak multiple sentences.")
#     wait_until_done()

#     speak("This will be interrupted.")
#     time.sleep(0.5)
#     stop()
#     speak("Interruption worked.")
#     wait_until_done()

#     shutdown()
#     print("[TEST] Done")
"""
Jarvis TTS – Simple Offline Engine using pyttsx3
with proper COM initialization for Windows threads.
"""

import warnings
warnings.filterwarnings("ignore")

import pyttsx3
import threading
import pythoncom  # Required for COM on Windows

_engine = None
_engine_lock = threading.Lock()
_initialized = False


def _ensure_com():
    """Ensure COM is initialized for the current thread."""
    try:
        pythoncom.CoInitialize()
    except Exception:
        # Already initialized or error – ignore
        pass


def _init_engine():
    """Initialize pyttsx3 engine with COM initialization."""
    global _engine, _initialized
    _ensure_com()
    try:
        engine = pyttsx3.init()
        
        # Configure voice (try to find a male voice)
        voices = engine.getProperty('voices')
        if voices:
            for voice in voices:
                if 'male' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            else:
                engine.setProperty('voice', voices[0].id)
        
        # Adjust speech rate
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate - 20)
        
        _engine = engine
        _initialized = True
        return True
    except Exception as exc:
        print(f"[TTS] Failed to initialize pyttsx3: {exc}")
        _initialized = False
        return False


def initialize() -> bool:
    """Initialize the TTS engine (call once, thread-safe)."""
    with _engine_lock:
        if _initialized and _engine is not None:
            return True
        return _init_engine()


def warm_up():
    """Warm up the engine (synchronous)."""
    if not _initialized:
        if not initialize():
            return
    try:
        print("[TTS] Warming up...")
        with _engine_lock:
            _engine.say("System online.")
            _engine.runAndWait()
        print("[TTS] Warmup complete")
    except Exception as exc:
        print(f"[TTS] Warmup failed: {exc}")


def speak(text: str):
    """Speak text synchronously (blocks until speech finishes)."""
    if not text or not text.strip():
        return
    
    # Ensure engine is initialized for this thread
    with _engine_lock:
        if not _initialized or _engine is None:
            if not _init_engine():
                print("[TTS] ERROR: Engine not available. Cannot speak.")
                return
    
    # Ensure COM is initialized for this thread (important for background threads)
    _ensure_com()
    
    try:
        print("[TTS] Speaking...")
        with _engine_lock:
            _engine.say(text)
            _engine.runAndWait()
    except Exception as exc:
        print(f"[TTS ERROR] Speech failed: {exc}")


def stop():
    """Stop current speech."""
    global _engine
    if _engine is not None:
        try:
            with _engine_lock:
                _engine.stop()
        except Exception:
            pass


def shutdown():
    """Clean shutdown."""
    global _engine, _initialized
    if _engine is not None:
        try:
            with _engine_lock:
                _engine.stop()
        except Exception:
            pass
        _engine = None
        _initialized = False
    # Uninitialize COM for the current thread (main thread)
    try:
        pythoncom.CoUninitialize()
    except Exception:
        pass
    print("[TTS] Shutdown complete")


def wait_until_done(timeout=None):
    """Compatibility function – always returns True."""
    return True


def ensure_audio_loop_started():
    """Compatibility function – does nothing."""
    pass


# ===============================
# STANDALONE TEST
# ===============================

if __name__ == "__main__":
    print("[TEST] Starting offline TTS test")
    try:
        initialize()
        warm_up()
        speak("Hello. This is Jarvis. Text to speech is online.")
        speak("I can speak multiple sentences.")
        print("[TEST] Done speaking")
    except KeyboardInterrupt:
        print("\n[TEST] Interrupted")
    finally:
        shutdown()
        print("[TEST] Done")