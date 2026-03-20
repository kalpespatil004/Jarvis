import subprocess
import os


# ---------------------------
# RUN SYSTEM COMMAND
# ---------------------------

def run_command(command):
    """
    Run a system command and return output
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        if result.stdout:
            return f"✅ Output:\n{result.stdout}"
        if result.stderr:
            return f"❌ Error:\n{result.stderr}"

        return "✅ Command executed successfully"

    except Exception as e:
        return f"❌ Failed to run command: {e}"


# ---------------------------
# RUN PYTHON FILE
# ---------------------------

def run_python_file(file_path):
    """
    Run a Python script
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"

        result = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True
        )

        if result.stdout:
            return f"🐍 Python Output:\n{result.stdout}"
        if result.stderr:
            return f"❌ Python Error:\n{result.stderr}"

        return "🐍 Python file executed successfully"

    except Exception as e:
        return f"❌ Error running Python file: {e}"


# ---------------------------
# OPEN COMMAND PROMPT
# ---------------------------

def open_cmd():
    """
    Open Windows Command Prompt
    """
    try:
        subprocess.Popen("cmd")
        return "💻 Command Prompt opened"
    except Exception as e:
        return f"❌ Error opening CMD: {e}"


# ---------------------------
# OPEN POWERSHELL
# ---------------------------

def open_powershell():
    """
    Open Windows PowerShell
    """
    try:
        subprocess.Popen("powershell")
        return "💻 PowerShell opened"
    except Exception as e:
        return f"❌ Error opening PowerShell: {e}"
