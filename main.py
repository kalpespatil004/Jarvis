"""
main.py
--------
J.A.R.V.I.S — Entry Point

Modes (set STARTUP_MODE in .env):
  ui    → Launch PyQt6 desktop GUI          (default)
  voice → Voice-only loop (no GUI)
  both  → GUI + background voice loop
"""

import sys
import os
import threading

# Load environment first
from dotenv import load_dotenv
load_dotenv()

try:
    from config import STARTUP_MODE, DEBUG_MODE, JARVIS_NAME, USER_NAME
except ImportError:
    STARTUP_MODE = "ui"
    DEBUG_MODE   = False
    JARVIS_NAME  = "Jarvis"
    USER_NAME    = "Sir"


def _print_banner():
    print("\n" + "═" * 60)
    print(f"   J.A.R.V.I.S  —  AI Assistant")
    print(f"   User  : {USER_NAME}")
    print(f"   Mode  : {STARTUP_MODE.upper()}")
    print(f"   Debug : {DEBUG_MODE}")
    print("═" * 60 + "\n")


def _start_background_services():
    """Start scheduler, sync manager, etc. in background threads."""
    # Reminder scheduler
    try:
        from services.automation.scheduler import start_scheduler
        from body.speak import speak
        start_scheduler(speak_fn=speak)
    except Exception as e:
        print(f"[MAIN] Scheduler error: {e}")

    # Memory sync
    try:
        from memory.sync_manager import start_sync
        start_sync()
    except Exception as e:
        print(f"[MAIN] Sync manager error: {e}")


def run_voice_mode():
    """Run Jarvis in voice-only mode (blocking)."""
    print("[MAIN] Starting voice mode...")
    try:
        from body.speak import warm_up, audio_loop
        from brain.brain import brain_loop

        warm_up()
        threading.Thread(target=brain_loop, daemon=True).start()
        audio_loop()  # blocking – runs in main thread

    except KeyboardInterrupt:
        print("\n[MAIN] Voice mode interrupted by user.")
    except Exception as e:
        print(f"[MAIN] Voice mode error: {e}")
        import traceback
        traceback.print_exc()


def run_ui_mode():
    """Run Jarvis in GUI mode (blocking)."""
    print("[MAIN] Starting UI mode...")
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("❌  PyQt6 not installed. Run: pip install pyqt6")
        print("   Falling back to voice mode...")
        run_voice_mode()
        return

    from ui.desktop.app import run
    sys.exit(run())


def run_both_mode():
    """Run GUI + background voice loop."""
    threading.Thread(target=_voice_background, daemon=True).start()
    run_ui_mode()


def _voice_background():
    """Voice loop running in background alongside UI."""
    try:
        from brain.brain import brain_loop
        brain_loop()
    except Exception as e:
        print(f"[MAIN] Background voice error: {e}")


# ────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _print_banner()
    _start_background_services()

    mode = STARTUP_MODE.lower()

    if mode == "voice":
        run_voice_mode()
    elif mode == "both":
        run_both_mode()
    else:
        run_ui_mode()   # default
