try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None


# ---------------------------
# BRIGHTNESS UP
# ---------------------------

def brightness_up(step=10):
    """
    Increase brightness by step%
    """
    if not sbc:
        return "❌ screen_brightness_control not installed"
    try:
        current = sbc.get_brightness(display=0)[0]
        new = min(100, current + step)
        sbc.set_brightness(new)
        return f"💡 Brightness increased to {new}%"
    except Exception as e:
        return f"❌ Error: {e}"


# ---------------------------
# BRIGHTNESS DOWN
# ---------------------------

def brightness_down(step=10):
    """
    Decrease brightness by step%
    """
    if not sbc:
        return "❌ screen_brightness_control not installed"
    try:
        current = sbc.get_brightness(display=0)[0]
        new = max(0, current - step)
        sbc.set_brightness(new)
        return f"💡 Brightness decreased to {new}%"
    except Exception as e:
        return f"❌ Error: {e}"


# ---------------------------
# SET BRIGHTNESS
# ---------------------------

def set_brightness(value):
    """
    Set brightness to a specific value (0-100)
    """
    if not sbc:
        return "❌ screen_brightness_control not installed"
    try:
        value = max(0, min(100, int(value)))
        sbc.set_brightness(value)
        return f"💡 Brightness set to {value}%"
    except Exception as e:
        return f"❌ Error: {e}"


# ---------------------------
# GET BRIGHTNESS
# ---------------------------

def get_brightness():
    """
    Get current brightness %
    """
    if not sbc:
        return "❌ screen_brightness_control not installed"
    try:
        current = sbc.get_brightness(display=0)[0]
        return f"💡 Current brightness is {current}%"
    except Exception as e:
        return f"❌ Error: {e}"
