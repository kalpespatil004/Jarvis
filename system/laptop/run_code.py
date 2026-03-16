"""
system/laptop/run_code.py
--------------------------
Run shell commands and Python scripts.
Cross-platform: Windows, Linux, macOS.
"""

import subprocess
import sys
import os
import platform

_PLATFORM = platform.system()


def run_command(command: str, timeout: int = 30) -> str:
    """Run a shell command and return output."""
    if not command:
        return "❌ No command provided."
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        out = result.stdout.strip()
        err = result.stderr.strip()

        if result.returncode != 0 and err:
            return f"⚠️ Command output:\n{err}"
        return f"✅ Output:\n{out}" if out else "✅ Command executed (no output)."
    except subprocess.TimeoutExpired:
        return "⏱️ Command timed out."
    except Exception as e:
        return f"❌ Command failed: {e}"


def run_python_file(filepath: str) -> str:
    """Run a Python script file."""
    if not filepath:
        return "❌ No file path provided."
    if not os.path.exists(filepath):
        return f"❌ File not found: {filepath}"
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=60
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if err:
            return f"⚠️ Script error:\n{err}"
        return f"✅ Script output:\n{out}" if out else "✅ Script ran successfully."
    except subprocess.TimeoutExpired:
        return "⏱️ Script timed out."
    except Exception as e:
        return f"❌ Script failed: {e}"


def open_cmd() -> str:
    """Open system terminal/command prompt."""
    try:
        if _PLATFORM == "Windows":
            subprocess.Popen("start cmd", shell=True)
        elif _PLATFORM == "Darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
        else:
            for terminal in ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]:
                if subprocess.run(["which", terminal], capture_output=True).returncode == 0:
                    subprocess.Popen([terminal])
                    break
        return "💻 Terminal opened."
    except Exception as e:
        return f"❌ Could not open terminal: {e}"


def open_powershell() -> str:
    """Open PowerShell (Windows only)."""
    if _PLATFORM != "Windows":
        return "PowerShell is only available on Windows."
    try:
        subprocess.Popen("start powershell", shell=True)
        return "💻 PowerShell opened."
    except Exception as e:
        return f"❌ Could not open PowerShell: {e}"
