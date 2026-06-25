import re
import socket

from LLM.offlineLLM import chat as offline_chat
from LLM.onlineLLM import chat as online_chat


# =========================
# COMPRESSED SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = (
    "ROLE: JARVIS\n"
    "USER: Kalpesh (aka Iron Man)\n"
    "STYLE: short, informative, polite, confident\n"
    "RULES: stay in character, no AI disclaimers\n"
)

SHORT_MODE_PROMPT = (
    "Reply in ONE sentence only.\n"
    "Maximum 20 words.\n"
    "Do not use bullet points.\n"
    "Do not add unnecessary explanation.\n"
)


# =========================
# INTERNET CHECK
# =========================
def _has_internet(host="8.8.8.8", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text))


def _build_prompt(user_prompt: str) -> str:
    system_prompt = SYSTEM_PROMPT
    if _word_count(user_prompt) <= 2:
        system_prompt += SHORT_MODE_PROMPT
    return f"{system_prompt}\nUser: {user_prompt}\nJARVIS:"


# =========================
# MAIN CHAT FUNCTION
# =========================
def chat(prompt: str) -> str:
    if not prompt or not prompt.strip():
        return "Please say something meaningful."

    user_prompt = prompt.strip()
    final_prompt = _build_prompt(user_prompt)

    # ---------- ONLINE PATH ----------
    if _has_internet():
        reply = online_chat(final_prompt)

        # If online fails, fallback
        if reply in ("OPENROUTER_UNAVAILABLE", None, ""):
            return offline_chat(final_prompt)

        return reply

    # ---------- OFFLINE PATH ----------
    return offline_chat(final_prompt)


# =========================
# MANUAL TEST
# =========================
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        print("Jarvis:", chat(user_input))
