from __future__ import annotations

import re
import threading
import time
from typing import Any

from memory.conversation import get_recent_turns


class ConversationManager:
    SESSION_TIMEOUT_SECONDS = 10 * 60
    CONVERSATION_TURNS = 6

    SYSTEM_PROMPT = (
        "You are Jarvis.\n"
        "You are already in an ongoing conversation.\n"
        "Never greet repeatedly.\n"
        "Never introduce yourself unless asked.\n"
        "Do not say \"Good morning\", \"Good evening\", or \"Hello\" unless:\n"
        "• this is the first message\n"
        "• user greeted first\n"
        "• conversation restarted.\n"
        "Use short, informative, polite, confident language.\n"
    )

    SHORT_MODE_PROMPT = (
        "Reply in exactly one sentence.\n"
        "Maximum 20 words.\n"
        "Do not use bullet points.\n"
        "Be concise.\n"
    )

    def __init__(self):
        self._lock = threading.Lock()
        self._last_activity: float | None = None
        self._startup = True

    def _word_count(self, text: str) -> int:
        return len(re.findall(r"\b\w+\b", text))

    def is_short_answer(self, text: str) -> bool:
        return self._word_count(text.strip()) <= 2

    def mark_activity(self) -> None:
        with self._lock:
            self._last_activity = time.monotonic()
            self._startup = False

    def has_session_timed_out(self) -> bool:
        with self._lock:
            if self._startup or self._last_activity is None:
                return True
            return time.monotonic() - self._last_activity > self.SESSION_TIMEOUT_SECONDS

    def should_restart_session(self) -> bool:
        return self.has_session_timed_out()

    def build_llm_prompt(self, user_text: str) -> str:
        text = user_text.strip()
        short_mode = self.is_short_answer(text)

        prompt_parts: list[str] = [self.SYSTEM_PROMPT]

        if self.should_restart_session():
            prompt_parts.append("This is the first message in a new session after inactivity.")
        else:
            prompt_parts.append(
                "Continue the existing conversation. Do not repeat greetings or reintroduce yourself."
            )

        if short_mode:
            prompt_parts.append(self.SHORT_MODE_PROMPT)

        history = get_recent_turns(self.CONVERSATION_TURNS)
        if history:
            prompt_parts.append("Conversation history:")
            for turn in history:
                prompt_parts.append(f"User: {turn['user_text']}")
                prompt_parts.append(f"Jarvis: {turn['assistant_text']}")

        prompt_parts.append(f"User: {text}")
        prompt_parts.append("Jarvis:")
        return "\n".join(prompt_parts)


conversation_manager = ConversationManager()
