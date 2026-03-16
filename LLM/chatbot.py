"""
chatbot.py
----------
Smart LLM router:
  Online  → Gemini → OpenRouter (fallbacks)
  Offline → Ollama
"""

import socket

from LLM.offlineLLM import chat as offline_chat
from LLM.onlineLLM  import chat as online_chat

try:
    from config import USER_NAME, USER_ALIAS, JARVIS_NAME
except ImportError:
    USER_NAME   = "Kalpesh"
    USER_ALIAS  = "Iron Man"
    JARVIS_NAME = "Jarvis"

SYSTEM_PROMPT = (
    f"ROLE: {JARVIS_NAME}\n"
    f"USER: {USER_NAME} (aka {USER_ALIAS})\n"
    "STYLE: short, informative, polite, confident, witty\n"
    "RULES: stay in character, no AI disclaimers, never say 'as an AI'\n"
)

_online_primed = False


def _has_internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 2) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def chat(prompt: str) -> str:
    global _online_primed

    if not prompt or not prompt.strip():
        return "Please say something meaningful."

    if _has_internet():
        if not _online_primed:
            try:
                _ = online_chat(SYSTEM_PROMPT + "\nReply only with: ACK")
                _online_primed = True
            except Exception:
                pass

        reply = online_chat(prompt)

        if reply in ("OPENROUTER_UNAVAILABLE", None, ""):
            return offline_chat(SYSTEM_PROMPT + "\nUser: " + prompt + "\nJARVIS:")

        return reply

    return offline_chat(SYSTEM_PROMPT + "\nUser: " + prompt + "\nJARVIS:")


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        print(f"{JARVIS_NAME}:", chat(user_input))
