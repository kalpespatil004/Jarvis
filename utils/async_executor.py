# utils/async_executor.py

import threading

def run_async(func, *args, **kwargs):
    thread = threading.Thread(
        target=func,
        args=args,
        kwargs=kwargs,
        daemon=True
    )
    thread.start()
    return thread