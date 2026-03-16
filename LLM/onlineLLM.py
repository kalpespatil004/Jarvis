"""
onlineLLM.py
------------
Primary online LLM: Google Gemini.
Falls back to OpenRouter when Gemini fails.
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from config import GEMINI_API_KEY, ONLINE_LLM_MODEL
except ImportError:
    GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
    ONLINE_LLM_MODEL  = "gemini-2.5-flash"

from LLM.openrouterLLM import chat as openrouter_chat

# ── Gemini setup ────────────────────────────────────────────
chat_session = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
        model = genai.GenerativeModel(ONLINE_LLM_MODEL)  # type: ignore
        chat_session = model.start_chat(history=[])
        print(f"[LLM] Gemini {ONLINE_LLM_MODEL} loaded.")
    except Exception as e:
        print(f"[LLM] Gemini init failed: {e}")
        chat_session = None
else:
    print("[LLM] No GEMINI_API_KEY set. Falling back to OpenRouter.")


def chat(prompt: str) -> str:
    if not chat_session:
        return openrouter_chat(prompt)

    if not prompt or not prompt.strip():
        return "Say something meaningful."

    try:
        response = chat_session.send_message(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[LLM] Gemini error: {e}. Falling back to OpenRouter.")
        return openrouter_chat(prompt)
