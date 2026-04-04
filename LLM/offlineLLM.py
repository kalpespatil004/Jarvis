"""
offlineLLM.py
-------------
Offline LLM chat using Ollama.
"""

import subprocess

_MODEL_NAME = "llama3.2:3b"
_TIMEOUT = 60  # increased for model load time


def chat(prompt: str) -> str:
    """
    Send prompt to offline LLM and return response.
    """
    if not prompt or not prompt.strip():
        return "Say something meaningful."

    try:
        result = subprocess.run(
            ["C:\\Users\\kalpe\\AppData\\Local\\Programs\\Ollama\\ollama.exe", "run", _MODEL_NAME, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_TIMEOUT
        )

        output = result.stdout.strip()

        if not output:
            return "I thought about it, but got nothing."

        return output

    except subprocess.TimeoutExpired:
        return "Thinking took too long. Try again."

    except FileNotFoundError:
        return "Offline model engine is not installed."

    except Exception:
        return "Offline language model failed unexpectedly."


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        response = chat(user_input)
        print(f"Jarvis: {response}")