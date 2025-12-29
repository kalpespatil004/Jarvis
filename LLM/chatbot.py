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

# Session state (important)
_online_primed = False


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


# =========================
# MAIN CHAT FUNCTION
# =========================
def chat(prompt: str) -> str:
    global _online_primed

    if not prompt or not prompt.strip():
        return "Please say something meaningful."

    # ---------- ONLINE PATH ----------
    if _has_internet():
        # Prime the model ONCE
        if not _online_primed:
            prime_text = SYSTEM_PROMPT + "\nReply only with: ACK"
            _ = online_chat(prime_text)
            _online_primed = True

        reply = online_chat(prompt)

        # If online fails, fallback
        if reply in ("OPENROUTER_UNAVAILABLE", None, ""):
            return offline_chat(SYSTEM_PROMPT + "\nUser: " + prompt + "\nJARVIS:")

        return reply

    # ---------- OFFLINE PATH ----------
    return offline_chat(SYSTEM_PROMPT + "\nUser: " + prompt + "\nJARVIS:")


# =========================
# MANUAL TEST
# =========================
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        print("Jarvis:", chat(user_input))
