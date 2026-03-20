"""Chat/advice service wrappers."""

from __future__ import annotations


def chat_response(text: str) -> str:
    from LLM.chatbot import chat

    return chat(text)
