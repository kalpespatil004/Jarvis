"""
onlineLLM.py
------------
Primary online LLM (Gemini).
Falls back to OpenRouter when Gemini fails.
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os
from dotenv import load_dotenv
import google.generativeai as genai

from LLM.openrouterLLM import chat as openrouter_chat

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY) # pyright: ignore[reportPrivateImportUsage]
    model = genai.GenerativeModel("gemini-2.5-flash") # type: ignore
    chat_session = model.start_chat(history=[])
else:
    chat_session = None


def chat(prompt: str) -> str:
    if not chat_session:
        return openrouter_chat(prompt)

    if not prompt or not prompt.strip():
        return "Say something meaningful."

    try:
        response = chat_session.send_message(prompt)
        return response.text.strip()
    except Exception:
        # Explicit fallback
        return openrouter_chat(prompt)
