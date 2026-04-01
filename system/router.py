# ---------------------------
# ROUTER: Map intents → modules
# ---------------------------

# Laptop modules
from system.laptop.app_launcher import open_app
from system.laptop.window_manager import (
    minimize_window, maximize_window, restore_window,
    close_window, focus_window, move_window, resize_window
)
from system.laptop.volume import volume_up, volume_down, set_volume, get_volume
from system.laptop.brightness import brightness_up, brightness_down, set_brightness, get_brightness
from system.laptop.process import list_processes, kill_process_by_name, kill_process_by_pid, is_process_running
from system.laptop.file_manager import (
    list_files, create_folder, create_file, delete_item,
    move_file, copy_file, search_file, file_info
)
from system.laptop.run_code import run_command, run_python_file, open_cmd, open_powershell
from system.laptop.screenshot import take_screenshot


# ---------------------------
# ROUTE FUNCTION
# ---------------------------

def route(intent, name=None, content=None, destination=None):
    """
    Route the detected intent to proper module function
    """
    try:
        # ----------------- Laptop -----------------
        if intent == "open_app":
            return open_app(name)

        elif intent == "minimize":
            return minimize_window()
        elif intent == "maximize":
            return maximize_window()
        elif intent == "restore":
            return restore_window()
        elif intent == "close":
            return close_window()
        elif intent == "focus":
            return focus_window(name)
        elif intent == "move_window":
            return move_window()
        elif intent == "resize_window":
            return resize_window()

        elif intent == "volume_up":
            return volume_up()
        elif intent == "volume_down":
            return volume_down()
        elif intent == "set_volume":
            return set_volume(name)
        elif intent == "get_volume":
            return get_volume()

        elif intent == "brightness_up":
            return brightness_up()
        elif intent == "brightness_down":
            return brightness_down()
        elif intent == "set_brightness":
            return set_brightness(name)
        elif intent == "get_brightness":
            return get_brightness()

        elif intent == "list_processes":
            return list_processes()
        elif intent == "kill_process":
            return kill_process_by_name(name)
        elif intent == "kill_pid":
            return kill_process_by_pid(name)
        elif intent == "check_process":
            return is_process_running(name)

        elif intent == "list_files":
            return list_files()
        elif intent == "create_folder":
            return create_folder(name)
        elif intent == "create_file":
            return create_file(name)
        elif intent == "delete":
            return delete_item(name)
        elif intent == "move":
            return move_file(name, destination)
        elif intent == "copy":
            return copy_file(name, destination)
        elif intent == "search":
            return search_file(name)
        elif intent == "file_info":
            return file_info(name)

        elif intent == "run_command":
            return run_command(name)
        elif intent == "run_python":
            return run_python_file(name)
        elif intent == "open_cmd":
            return open_cmd()
        elif intent == "open_powershell":
            return open_powershell()

        elif intent == "take_screenshot":
            return take_screenshot()

        

        else:
            return "❓ Command not supported"

    except Exception as e:
        return f"❌ Error in router: {e}"
