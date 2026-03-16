"""
utils/constants.py  –  Global constants & enums
"""

from enum import Enum, auto


class JarvisMode(Enum):
    VOICE = auto()
    UI    = auto()
    BOTH  = auto()


class Intent(str, Enum):
    # Time
    GET_TIME      = "get_time"
    GET_DATE      = "get_date"
    # Services
    GET_WEATHER   = "get_weather"
    GET_NEWS      = "get_news"
    GET_CRYPTO    = "get_crypto"
    SEARCH_YOUTUBE= "search_youtube"
    DICTIONARY    = "dictionary"
    # System – laptop
    OPEN_APP      = "open_app"
    VOLUME_UP     = "volume_up"
    VOLUME_DOWN   = "volume_down"
    SET_VOLUME    = "set_volume"
    GET_VOLUME    = "get_volume"
    MUTE          = "mute"
    BRIGHTNESS_UP = "brightness_up"
    BRIGHTNESS_DOWN= "brightness_down"
    SET_BRIGHTNESS = "set_brightness"
    TAKE_SCREENSHOT= "take_screenshot"
    MINIMIZE_WINDOW= "minimize_window"
    MAXIMIZE_WINDOW= "maximize_window"
    CLOSE_WINDOW   = "close_window"
    RESTORE_WINDOW = "restore_window"
    KILL_PROCESS   = "kill_process"
    LIST_PROCESSES = "list_processes"
    LIST_FILES     = "list_files"
    CREATE_FOLDER  = "create_folder"
    DELETE_ITEM    = "delete_item"
    SEARCH_FILE    = "search_file"
    RUN_COMMAND    = "run_command"
    # Mobile
    GET_LOCATION   = "get_location"
    SEND_SMS       = "send_sms"
    READ_NOTIFICATIONS = "read_notifications"
    # Memory
    RECALL_MEMORY  = "recall_memory"
    SAVE_MEMORY    = "save_memory"
    # Vault
    VAULT_OPEN     = "vault_open"
    VAULT_STORE    = "vault_store"
    VAULT_RETRIEVE = "vault_retrieve"
    # Automation
    SET_REMINDER   = "set_reminder"
    SET_ALARM      = "set_alarm"
    SCHEDULE_TASK  = "schedule_task"
    # Misc
    SYSTEM_INFO    = "system_info"
    CALCULATE      = "calculate"
    PLAY_MUSIC     = "play_music"
    STOP_MUSIC     = "stop_music"
    # LLM
    CHAT           = "chat"
    UNKNOWN        = "unknown"
    EXIT           = "exit"


# Colors used in UI
JARVIS_BLUE      = "#00BFFF"
JARVIS_DARK      = "#0a0a1a"
JARVIS_DARK2     = "#0f0f2e"
JARVIS_ACCENT    = "#1a1a3e"
JARVIS_GREEN     = "#00ff88"
JARVIS_TEXT      = "#e0e0ff"
JARVIS_SUBTEXT   = "#8888aa"
