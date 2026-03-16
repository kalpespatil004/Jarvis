"""
system/laptop/brightness.py
-----------------------------
Cross-platform screen brightness control.
Windows : screen_brightness_control library
Linux   : brightnessctl or xrandr
macOS   : brightness CLI or osascript
"""

import os
import platform

_PLATFORM = platform.system()


def _get_sbc():
    try:
        import screen_brightness_control as sbc
        return sbc
    except ImportError:
        return None


def get_brightness() -> str:
    sbc = _get_sbc()
    if sbc:
        try:
            level = sbc.get_brightness(display=0)
            val = level[0] if isinstance(level, list) else level
            return f"💡 Current brightness is {val}%"
        except Exception as e:
            return f"❌ Brightness read failed: {e}"

    if _PLATFORM == "Linux":
        try:
            result = os.popen("brightnessctl g").read().strip()
            max_r  = os.popen("brightnessctl m").read().strip()
            if result and max_r:
                pct = int(int(result) / int(max_r) * 100)
                return f"💡 Current brightness is {pct}%"
        except Exception:
            pass

    return "❌ Brightness control not available on this system."


def set_brightness(value: int) -> str:
    value = max(0, min(100, int(value)))
    sbc = _get_sbc()
    if sbc:
        try:
            sbc.set_brightness(value, display=0)
            return f"💡 Brightness set to {value}%"
        except Exception as e:
            return f"❌ Failed to set brightness: {e}"

    if _PLATFORM == "Linux":
        try:
            os.system(f"brightnessctl s {value}%")
            return f"💡 Brightness set to {value}%"
        except Exception as e:
            return f"❌ brightnessctl error: {e}"

    if _PLATFORM == "Darwin":
        try:
            os.system(f"brightness {value/100:.2f}")
            return f"💡 Brightness set to {value}%"
        except Exception:
            pass

    return "❌ Cannot set brightness on this platform."


def brightness_up(step: int = 10) -> str:
    sbc = _get_sbc()
    if sbc:
        try:
            current = sbc.get_brightness(display=0)
            val = current[0] if isinstance(current, list) else current
            return set_brightness(min(100, val + step))
        except Exception as e:
            return f"❌ Brightness up failed: {e}"
    return set_brightness(60)  # safe default


def brightness_down(step: int = 10) -> str:
    sbc = _get_sbc()
    if sbc:
        try:
            current = sbc.get_brightness(display=0)
            val = current[0] if isinstance(current, list) else current
            return set_brightness(max(0, val - step))
        except Exception as e:
            return f"❌ Brightness down failed: {e}"
    return set_brightness(40)  # safe default
