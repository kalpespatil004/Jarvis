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
    if not client:
        return "OPENROUTER_UNAVAILABLE"

    if not prompt or not prompt.strip():
        return "Say something meaningful."

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1-0528:free",
            messages=[
                {"role": "system", "content": "You are JARVIS. Be concise, calm, intelligent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip() # type: ignore
    except Exception:
        return "OPENROUTER_UNAVAILABLE"
