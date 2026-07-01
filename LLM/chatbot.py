import re
import socket

from LLM.offlineLLM import chat as offline_chat
from LLM.onlineLLM import chat as online_chat


# =========================
# COMPRESSED SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = (
    "ROLE: JARVIS\n"
    "USER: Kalpesh Patil\n"
    "STYLE: very short, informative, polite, confident\n"
    "RULES: no AI disclaimers\n"
    "do not greet \n"
    "do not call kalpesh patil name on every response use my name when it needed \n"
    

    
   
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


def _strip_greeting(text: str) -> str:
    if not text:
        return text

    # Remove common leading salutations and honorifics like "Good morning, Tony.", "Hello, Mr. Iron Man!"
    # This is intentionally conservative: only removes short leading salutations up to the first sentence boundary.
    import re

    # Patterns like "Good morning, Tony." or "Hello Tony," or "Hi, Sir." at the start
    greeting_re = re.compile(r"^(\s*(good\s+morning|good\s+afternoon|good\s+evening|hello|hi|hey)\b[\s,!\.-]{0,5}[^\.\n,]{0,40}[\.,!\-]?\s*)", re.IGNORECASE)
    stripped = greeting_re.sub("", text, count=1).strip()

    # Also handle short honorifics like "Mr. Iron Man," or "Tony," at the start
    honorific_re = re.compile(r"^(\s*(mr|mrs|ms|sir|madam|dr)\.?\s+[^,\n]{1,40},\s*)", re.IGNORECASE)
    stripped = honorific_re.sub("", stripped, count=1).strip()

    return stripped or text


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
            offline_reply = offline_chat(final_prompt)
            return _strip_greeting(offline_reply)

        return _strip_greeting(reply)

    # ---------- OFFLINE PATH ----------
    return _strip_greeting(offline_chat(final_prompt))


# =========================
# MANUAL TEST
# =========================
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        print("Jarvis:", chat(user_input))
