"""
memory/sync_manager.py
----------------------
Syncs local JSON cache ↔ Firebase Firestore (when available).
Runs silently in background; never blocks the main thread.
"""

import threading
import time

_sync_running = False
_SYNC_INTERVAL = 300  # seconds


def _sync_once():
    """Attempt a single sync cycle."""
    try:
        from config import FIREBASE_CRED_PATH
        if not FIREBASE_CRED_PATH:
            return

        import firebase_admin
        from firebase_admin import credentials, firestore
        from memory.local_cache import read_cache

        # Initialize only once
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CRED_PATH)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        cache_data = read_cache()

        # Push local data to Firestore
        db.collection("jarvis").document("cache").set(cache_data)

    except ImportError:
        pass  # firebase_admin not installed
    except Exception as e:
        print(f"[SYNC] Sync error: {e}")


def _sync_loop():
    global _sync_running
    while _sync_running:
        _sync_once()
        time.sleep(_SYNC_INTERVAL)


def start_sync():
    """Start background sync thread."""
    global _sync_running
    if _sync_running:
        return
    _sync_running = True
    t = threading.Thread(target=_sync_loop, daemon=True)
    t.start()
    print("[SYNC] Background sync started.")


def stop_sync():
    global _sync_running
    _sync_running = False


def force_sync():
    """Trigger an immediate sync."""
    threading.Thread(target=_sync_once, daemon=True).start()
