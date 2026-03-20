import os
from datetime import datetime

try:
    import pyautogui
except ImportError:
    pyautogui = None


# ---------------------------
# CONFIGURATION
# ---------------------------

SCREENSHOT_DIR = "screenshots"


def _ensure_dir():
    """
    Ensure screenshot directory exists
    """
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)


def _filename(prefix="screenshot"):
    """
    Generate timestamped filename
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(SCREENSHOT_DIR, f"{prefix}_{ts}.png")


# ---------------------------
# SCREENSHOT FUNCTIONS
# ---------------------------

def take_screenshot():
    """
    Takes a full-screen screenshot
    """
    if not pyautogui:
        return "❌ pyautogui not installed (pip install pyautogui)"

    try:
        _ensure_dir()
        path = _filename("fullscreen")
        pyautogui.screenshot(path)
        return f"📸 Full-screen screenshot saved: {path}"
    except Exception as e:
        return f"❌ Screenshot failed: {e}"


def take_active_window():
    """
    Takes screenshot of the currently active window (best-effort)
    """
    if not pyautogui:
        return "❌ pyautogui not installed (pip install pyautogui)"

    try:
        _ensure_dir()
        # Best-effort: capture mouse-focused window area
        x, y = pyautogui.position()
        img = pyautogui.screenshot()
        path = _filename("active_window")
        img.save(path)
        return f"🪟 Active window screenshot saved: {path}"
    except Exception as e:
        return f"❌ Active window screenshot failed: {e}"


def take_region(x, y, width, height):
    """
    Takes screenshot of a specific region
    """
    if not pyautogui:
        return "❌ pyautogui not installed (pip install pyautogui)"

    try:
        _ensure_dir()
        path = _filename("region")
        pyautogui.screenshot(path, region=(x, y, width, height))
        return f"🖼️ Region screenshot saved: {path}"
    except Exception as e:
        return f"❌ Region screenshot failed: {e}"


def list_screenshots():
    """
    Lists saved screenshots
    """
    if not os.path.exists(SCREENSHOT_DIR):
        return "📂 No screenshots taken yet"

    files = os.listdir(SCREENSHOT_DIR)
    if not files:
        return "📂 No screenshots found"

    return "📂 Screenshots:\n" + "\n".join(files)
