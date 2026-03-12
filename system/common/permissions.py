import os
import ctypes
import platform

# ---------------------------
# BASIC SYSTEM PERMISSIONS
# ---------------------------

def is_windows():
    return platform.system().lower() == "windows"


def is_admin():
    """
    Checks whether Jarvis is running with administrator privileges
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


# ---------------------------
# FEATURE-LEVEL PERMISSIONS
# ---------------------------

FEATURE_PERMISSIONS = {
    "open_app": True,
    "volume_control": True,
    "screenshot": True,
    "process": True,
    "file_access": True,
    "brightness": False,   # requires admin or hardware API
    "camera": False,       # mobile only
    "gps": False           # mobile only
}


def has_permission(feature: str):
    """
    Checks if a specific feature is allowed
    """
    return FEATURE_PERMISSIONS.get(feature, False)


def require_admin(feature: str):
    """
    Checks if feature requires admin rights
    """
    admin_required = ["brightness", "process"]
    if feature in admin_required:
        return is_admin()
    return True


# ---------------------------
# MASTER PERMISSION CHECK
# ---------------------------

def check_permission(feature: str):
    """
    Final permission validator for Jarvis features
    """
    if not is_windows():
        return False, "❌ Unsupported OS"

    if not has_permission(feature):
        return False, f"❌ Permission denied for {feature}"

    if not require_admin(feature):
        return False, "❌ Admin rights required"

    return True, "✅ Permission granted"
