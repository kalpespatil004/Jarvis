import datetime
import traceback

# ---------------------------
# BASE JARVIS ERROR
# ---------------------------

class JarvisError(Exception):
    """
    Base exception for all Jarvis-related errors
    """
    def __init__(self, message="Jarvis error occurred"):
        super().__init__(message)
        self.message = message
        self.timestamp = datetime.datetime.now()

    def __str__(self):
        return f"[{self.timestamp}] {self.message}"


# ---------------------------
# SPECIFIC ERROR TYPES
# ---------------------------

class PermissionDeniedError(JarvisError):
    def __init__(self, feature):
        super().__init__(f"Permission denied for feature: {feature}")


class UnsupportedOSError(JarvisError):
    def __init__(self, os_name):
        super().__init__(f"Unsupported Operating System: {os_name}")


class AppNotFoundError(JarvisError):
    def __init__(self, app):
        super().__init__(f"Application not found: {app}")


class FeatureNotSupportedError(JarvisError):
    def __init__(self, feature):
        super().__init__(f"Feature not supported: {feature}")


class ExecutionError(JarvisError):
    def __init__(self, feature, error):
        super().__init__(f"Error executing {feature}: {error}")


# ---------------------------
# ERROR LOGGER
# ---------------------------

def log_error(error: Exception, logfile="jarvis_error.log"):
    """
    Logs errors to a file for debugging and audit
    """
    with open(logfile, "a") as f:
        f.write("\n" + "="*50 + "\n")
        f.write(str(datetime.datetime.now()) + "\n")
        f.write(str(error) + "\n")
        f.write(traceback.format_exc())
