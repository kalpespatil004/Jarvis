"""
offlineLLM.py
-------------
Offline LLM chat using Ollama.
Uses config for path instead of hardcoded Windows path.
"""

import subprocess

try:
    from config import OLLAMA_PATH, OFFLINE_LLM_MODEL
except ImportError:
    import os
    OLLAMA_PATH = (
        r"C:\Users\kalpe\AppData\Local\Programs\Ollama\ollama.exe"
        if os.name == "nt" else "ollama"
    )
    OFFLINE_LLM_MODEL = "phi"

_TIMEOUT = 60


def chat(prompt: str) -> str:
    """Send prompt to offline Ollama LLM and return response."""
    if not prompt or not prompt.strip():
        return "Say something meaningful."

    try:
        result = subprocess.run(
            [OLLAMA_PATH, "run", OFFLINE_LLM_MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT
        )
        output = result.stdout.strip()
        if not output:
            return "I thought about it, but got nothing."
        return output

    except subprocess.TimeoutExpired:
        return "Thinking took too long. Try again."
    except FileNotFoundError:
        return "Offline model engine is not installed. Please install Ollama."
    except Exception:
        return "Offline language model failed unexpectedly."


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        print("Jarvis:", chat(user_input))
