"""
system/laptop/window_manager.py
---------------------------------
Cross-platform window management.
Windows : pygetwindow + pyautogui
Linux   : wmctrl / xdotool
"""

import os
import platform

_PLATFORM = platform.system()


def _pygetwindow():
    try:
        import pygetwindow as gw
        return gw
    except ImportError:
        return None


def minimize_window() -> str:
    gw = _pygetwindow()
    if gw:
        try:
            wins = gw.getAllWindows()
            active = [w for w in wins if w.isActive]
            if active:
                active[0].minimize()
                return "🪟 Window minimized."
        except Exception as e:
            return f"❌ Minimize failed: {e}"

    if _PLATFORM == "Linux":
        os.system("wmctrl -r :ACTIVE: -b add,hidden")
        return "🪟 Window minimized."

    return "❌ Window management not available."


def maximize_window() -> str:
    gw = _pygetwindow()
    if gw:
        try:
            wins = gw.getAllWindows()
            active = [w for w in wins if w.isActive]
            if active:
                active[0].maximize()
                return "🪟 Window maximized."
        except Exception as e:
            return f"❌ Maximize failed: {e}"

    if _PLATFORM == "Linux":
        os.system("wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz")
        return "🪟 Window maximized."

    return "❌ Window management not available."


def restore_window() -> str:
    gw = _pygetwindow()
    if gw:
        try:
            wins = gw.getAllWindows()
            active = [w for w in wins if w.isActive]
            if active:
                active[0].restore()
                return "🪟 Window restored."
        except Exception as e:
            return f"❌ Restore failed: {e}"

    if _PLATFORM == "Linux":
        os.system("wmctrl -r :ACTIVE: -b remove,maximized_vert,maximized_horz")
        return "🪟 Window restored."

    return "❌ Window management not available."


def close_window() -> str:
    try:
        import pyautogui
        import time
        pyautogui.hotkey("alt", "F4")
        return "🪟 Window closed."
    except ImportError:
        pass

    if _PLATFORM == "Linux":
        os.system("wmctrl -c :ACTIVE:")
        return "🪟 Window closed."

    return "❌ Cannot close window on this platform."


def focus_window(title: str) -> str:
    if not title:
        return "❌ Please specify a window title."
    gw = _pygetwindow()
    if gw:
        try:
            wins = gw.getWindowsWithTitle(title)
            if wins:
                wins[0].activate()
                return f"🪟 Focused window: {title}"
            return f"❌ No window found with title: {title}"
        except Exception as e:
            return f"❌ Focus failed: {e}"

    if _PLATFORM == "Linux":
        os.system(f"wmctrl -a '{title}'")
        return f"🪟 Attempting to focus: {title}"

    return "❌ Focus not supported on this platform."


def move_window(x: int = 100, y: int = 100) -> str:
    try:
        import pyautogui
        pyautogui.hotkey("win", "left")
        return "🪟 Window moved."
    except Exception as e:
        return f"❌ Move failed: {e}"


def resize_window(width: int = 800, height: int = 600) -> str:
    gw = _pygetwindow()
    if gw:
        try:
            wins = gw.getAllWindows()
            active = [w for w in wins if w.isActive]
            if active:
                active[0].resizeTo(width, height)
                return f"🪟 Window resized to {width}×{height}."
        except Exception as e:
            return f"❌ Resize failed: {e}"
    return "❌ Resize not supported."
