import pyautogui
import pygetwindow as gw
import time


# ---------------------------
# GET ACTIVE WINDOW
# ---------------------------

def get_active_window():
    """
    Get currently active window
    """
    try:
        return gw.getActiveWindow()
    except Exception:
        return None


# ---------------------------
# MINIMIZE WINDOW
# ---------------------------

def minimize_window():
    """
    Minimize active window
    """
    window = get_active_window()
    if window:
        window.minimize()
        return "🪟 Window minimized"
    return "❌ No active window found"


# ---------------------------
# MAXIMIZE WINDOW
# ---------------------------

def maximize_window():
    """
    Maximize active window
    """
    window = get_active_window()
    if window:
        window.maximize()
        return "🪟 Window maximized"
    return "❌ No active window found"


# ---------------------------
# RESTORE WINDOW
# ---------------------------

def restore_window():
    """
    Restore minimized window
    """
    window = get_active_window()
    if window:
        window.restore()
        return "🪟 Window restored"
    return "❌ No active window found"


# ---------------------------
# CLOSE WINDOW
# ---------------------------

def close_window():
    """
    Close active window
    """
    try:
        pyautogui.hotkey("alt", "f4")
        return "❌ Window closed"
    except Exception as e:
        return f"❌ Error closing window: {e}"


# ---------------------------
# FOCUS WINDOW BY NAME
# ---------------------------

def focus_window(app_name):
    """
    Focus a window using app name
    """
    try:
        windows = gw.getWindowsWithTitle(app_name)
        if windows:
            windows[0].activate()
            return f"🎯 Focused on '{app_name}'"
        return f"⚠️ No window found with name '{app_name}'"
    except Exception as e:
        return f"❌ Error focusing window: {e}"


# ---------------------------
# MOVE WINDOW
# ---------------------------

def move_window(x=100, y=100):
    """
    Move active window
    """
    window = get_active_window()
    if window:
        window.moveTo(x, y)
        return f"📐 Window moved to ({x}, {y})"
    return "❌ No active window found"


# ---------------------------
# RESIZE WINDOW
# ---------------------------

def resize_window(width=800, height=600):
    """
    Resize active window
    """
    window = get_active_window()
    if window:
        window.resizeTo(width, height)
        return f"📐 Window resized to {width}x{height}"
    return "❌ No active window found"
