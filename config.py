"""
config.py
---------
Global configuration for Jarvis AI Assistant.
All settings are loaded from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ============================================================
# IDENTITY
# ============================================================
JARVIS_NAME = "Jarvis"
USER_NAME   = os.getenv("USER_NAME", "Kalpesh")
USER_ALIAS  = os.getenv("USER_ALIAS", "Iron Man")

# ============================================================
# API KEYS
# ============================================================
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NEWS_API_KEY        = os.getenv("NEWS_API_KEY", "")
FIREBASE_CRED_PATH  = os.getenv("FIREBASE_CRED_PATH", "")

# ============================================================
# LLM SETTINGS
# ============================================================
ONLINE_LLM_MODEL   = os.getenv("ONLINE_LLM_MODEL", "gemini-2.5-flash")
OFFLINE_LLM_MODEL  = os.getenv("OFFLINE_LLM_MODEL", "phi")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")

# Ollama executable path (auto-detected or set manually)
_default_ollama = (
    r"C:\Users\kalpe\AppData\Local\Programs\Ollama\ollama.exe"
    if os.name == "nt"
    else "ollama"
)
OLLAMA_PATH = os.getenv("OLLAMA_PATH", _default_ollama)

# ============================================================
# TTS SETTINGS
# ============================================================
TTS_MODEL       = os.getenv("TTS_MODEL", "tts_models/en/vctk/vits")
TTS_SPEAKER     = os.getenv("TTS_SPEAKER", "p228")
TTS_SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", "22050"))
USE_GPU         = os.getenv("USE_GPU", "auto")          # "auto" | "true" | "false"

# ============================================================
# STT / LISTEN SETTINGS
# ============================================================
VOSK_MODEL_PATH   = os.getenv("VOSK_MODEL_PATH", r"C:\Jarvis\body\vosk-model-en-in-0.5")
STT_SAMPLE_RATE   = int(os.getenv("STT_SAMPLE_RATE", "16000"))
STT_BLOCK_SIZE    = int(os.getenv("STT_BLOCK_SIZE", "4000"))

# ============================================================
# PATHS
# ============================================================
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR    = os.path.join(BASE_DIR, "database")
SCREENSHOT_DIR  = os.path.join(BASE_DIR, "screenshots")
LOGS_DIR        = os.path.join(BASE_DIR, "logs")
VAULT_DIR       = os.path.join(BASE_DIR, "vault_data")
ASSETS_DIR      = os.path.join(BASE_DIR, "assets")
AVATAR_DIR      = os.path.join(ASSETS_DIR, "avtar")

# Ensure critical directories exist
for _d in [DATABASE_DIR, SCREENSHOT_DIR, LOGS_DIR, VAULT_DIR]:
    os.makedirs(_d, exist_ok=True)

# ============================================================
# DATABASE FILES
# ============================================================
CACHE_DB_PATH = os.path.join(DATABASE_DIR, "cache.json")
VAULT_DB_PATH = os.path.join(DATABASE_DIR, "vault.db")

# ============================================================
# MEMORY SETTINGS
# ============================================================
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_HISTORY", "20"))
MEMORY_CONTEXT_WINDOW    = int(os.getenv("MEMORY_CONTEXT", "6"))  # last N turns injected into LLM

# ============================================================
# SERVICES DEFAULTS
# ============================================================
DEFAULT_WEATHER_CITY = os.getenv("DEFAULT_CITY", "Pune")
DEFAULT_NEWS_COUNTRY  = os.getenv("DEFAULT_COUNTRY", "in")
DEFAULT_CRYPTO_COIN   = os.getenv("DEFAULT_CRYPTO", "bitcoin")
DEFAULT_CRYPTO_CURR   = os.getenv("DEFAULT_CURRENCY", "inr")

# ============================================================
# MODES
# ============================================================
STARTUP_MODE = os.getenv("STARTUP_MODE", "ui")   # "ui" | "voice" | "both"
DEBUG_MODE   = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ============================================================
# AUTOMATION
# ============================================================
AUTOMATION_RULES_FILE = os.path.join(DATABASE_DIR, "automation_rules.json")
