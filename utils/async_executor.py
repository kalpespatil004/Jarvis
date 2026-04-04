"""
async_executor.py
-----------------
Utility to run functions asynchronously in background threads.
Used by brain.py to execute intents without blocking the voice loop.
"""

import threading


def run_async(func, *args, **kwargs) -> threading.Thread:
    """
    Run a function in a background daemon thread.

    Args:
        func (callable): Function to execute
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        threading.Thread: The started thread
    """
    thread = threading.Thread(
        target=_safe_run,
        args=(func, args, kwargs),
        daemon=True
    )
    thread.start()
    return thread


def _safe_run(func, args, kwargs):
    """
    Wrapper to catch and log exceptions inside threads.
    """
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(f"[ASYNC ERROR] {func.__name__}: {e}")