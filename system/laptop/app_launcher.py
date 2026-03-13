import subprocess
import platform
import os

# Optional: predefined paths for common apps
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "notepad": r"C:\Windows\system32\notepad.exe",
    "calculator": r"C:\Windows\System32\calc.exe",
    "cmd": r"C:\Windows\system32\cmd.exe",
    "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    "paint": r"C:\Windows\system32\mspaint.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"
}

def open_app(name):
    """
    Open any app by name.
    1. Try predefined path
    2. Try 'start' command (Windows)
    """
    name = name.lower()

    # 1️⃣ Try predefined path
    path = APP_PATHS.get(name)
    if path and os.path.exists(path):
        try:
            subprocess.Popen(path)
            return f"✅ Opening {name}"
        except Exception as e:
            return f"❌ Failed to open {name}: {e}"

    # 2️⃣ Try 'start' command for any app in PATH
    if platform.system() == "Windows":
        try:
            subprocess.Popen(f"start {name}", shell=True)
            return f"✅ Trying to open {name}"
        except Exception as e:
            return f"❌ Failed to open {name} using start command: {e}"

    return f"❌ App not found: {name}"
