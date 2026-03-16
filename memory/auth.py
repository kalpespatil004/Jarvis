"""
memory/auth.py
--------------
Simple PIN-based authentication for sensitive memory / vault access.
"""

import hashlib
import os
from memory.local_cache import read_cache, write_cache

_KEY = "auth_pin_hash"


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.strip().encode()).hexdigest()


def set_pin(pin: str) -> str:
    """Set or change the access PIN."""
    data = read_cache()
    data[_KEY] = _hash_pin(pin)
    write_cache(data)
    return "🔐 PIN set successfully."


def verify_pin(pin: str) -> bool:
    """Verify the access PIN. Returns True if correct."""
    data = read_cache()
    stored = data.get(_KEY)
    if not stored:
        return True  # No PIN set → open access
    return _hash_pin(pin) == stored


def is_pin_set() -> bool:
    data = read_cache()
    return _KEY in data


def remove_pin() -> str:
    data = read_cache()
    data.pop(_KEY, None)
    write_cache(data)
    return "🔓 PIN removed."
