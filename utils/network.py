"""
utils/network.py  –  Internet connectivity utilities
"""

import socket
import urllib.request


def has_internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 2) -> bool:
    """Fast internet check via TCP socket."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def get_public_ip() -> str:
    """Get public IP address."""
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode()
    except Exception:
        return "Unknown"


def ping(host: str, timeout: int = 3) -> bool:
    """Ping a host by attempting a TCP connection on port 80."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, 80))
        return True
    except Exception:
        return False
