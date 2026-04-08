import imp
import os
import subprocess

try:
    import psutil
except ImportError:
    psutil = None


# ---------------------------
# LIST PROCESSES
# ---------------------------

def list_processes(limit=15):
    """
    List currently running processes (limited output)
    """
    if not psutil:
        return "❌ psutil not installed (pip install psutil)"

    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            processes.append(f"{proc.info['pid']} : {proc.info['name']}")
            if len(processes) >= limit:
                break

        return "📋 Running Processes:\n" + "\n".join(processes)

    except Exception as e:
        return f"❌ Failed to list processes: {e}"


# ---------------------------
# KILL PROCESS BY NAME
# ---------------------------

def kill_process_by_name(name):
    """
    Kill a process using process name
    """
    if not psutil:
        return "❌ psutil not installed (pip install psutil)"

    killed = False
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                proc.kill()
                killed = True

        if killed:
            return f"❌ Process '{name}' terminated successfully"
        else:
            return f"⚠️ No process found with name '{name}'"

    except Exception as e:
        return f"❌ Error killing process: {e}"


# ---------------------------
# KILL PROCESS BY PID
# ---------------------------

def kill_process_by_pid(pid):
    """
    Kill a process using PID
    """
    if not psutil:
        return "❌ psutil not installed (pip install psutil)"

    try:
        p = psutil.Process(int(pid))
        p.kill()
        return f"❌ Process with PID {pid} terminated"

    except psutil.NoSuchProcess:
        return f"⚠️ No process with PID {pid}"
    except Exception as e:
        return f"❌ Error: {e}"


# ---------------------------
# CHECK IF PROCESS RUNNING
# ---------------------------

def is_process_running(name):
    """
    Check if a process is running
    """
    if not psutil:
        return "❌ psutil not installed (pip install psutil)"

    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and name.lower() in proc.info['name'].lower():
                return f"✅ Process '{name}' is running"
        return f"❌ Process '{name}' is NOT running"

    except Exception as e:
        return f"❌ Error checking process: {e}"

if __name__ == "__main__":
    import time
    time.sleep(5)   
    print(list_processes())
    time.sleep(5)
    print(kill_process_by_pid(14544))
    time.sleep(5)
    print(is_process_running("Chrome")) 
    time.sleep(5)
    print(kill_process_by_name("Chrome"))
    time.sleep(5)
    print(list_processes())
    