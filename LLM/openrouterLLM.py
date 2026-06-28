"""
openrouterLLM.py
----------------
OpenRouter DeepSeek R1 (free).
Secondary online LLM.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

# Simple cooldown after failures to avoid spamming unavailable service
_last_failure = 0.0
_cooldown_s = 60.0

if API_KEY:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Jarvis Assistant"
        }
    )
else:
    client = None


def chat(prompt: str) -> str:
    import time

    global _last_failure

    # If we previously failed recently, skip attempting
    if time.time() - _last_failure < _cooldown_s:
        return "OPENROUTER_UNAVAILABLE"

    if not client:
        _last_failure = time.time()
        return "OPENROUTER_UNAVAILABLE"

    if not prompt or not prompt.strip():
        return "Say something meaningful."

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are JARVIS. Be concise, calm, intelligent. Do not start replies with salutations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip() # type: ignore
    except Exception as e:
        print("OPENROUTER_UNAVAILABLE", e)
        _last_failure = time.time()
        return "OPENROUTER_UNAVAILABLE"

if __name__ == "__main__":
    while True:
        test_prompt = input("Test prompt: ")
        if test_prompt.lower() in ("exit", "quit"):
            break
        print(chat(test_prompt))