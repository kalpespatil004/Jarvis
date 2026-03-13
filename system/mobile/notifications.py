try:
    from plyer import notification
except ImportError:
    notification = None

from datetime import datetime
import os


# ---------------------------
# SHOW NOTIFICATION
# ---------------------------

def show_notification(title, message, timeout=5):
    """
    Display a system notification
    """
    if not notification:
        return "❌ plyer not installed"

    try:
        notification.notify(
            title=title,
            message=message,
            timeout=timeout
        )
        return "🔔 Notification shown"
    except Exception as e:
        return f"❌ Error showing notification: {e}"


# ---------------------------
# READ NOTIFICATION (SIMULATED)
# ---------------------------

def read_notification(message):
    """
    Read notification text (for TTS)
    """
    return f"📢 Notification says: {message}"


# ---------------------------
# LOG NOTIFICATION
# ---------------------------

def log_notification(title, message, log_dir="notification_logs"):
    """
    Save notification to a log file
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "notifications.txt")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now()}] {title}: {message}\n"
            )

        return "📝 Notification logged"

    except Exception as e:
        return f"❌ Error logging notification: {e}"
