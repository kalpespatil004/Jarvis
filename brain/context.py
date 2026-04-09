# brain/context.py

from collections import deque

# Intents that keep "volume" as the active dialogue domain for follow-ups.
_VOLUME_INTENTS = frozenset(
    {"volume_up", "volume_down", "set_volume", "get_volume", "volume_control"}
)
# Intents that keep "brightness" as the active dialogue domain.
_BRIGHTNESS_INTENTS = frozenset(
    {"brightness_up", "brightness_down", "set_brightness", "get_brightness", "brightness_control"}
)


class ContextManager:
    def __init__(self, max_history: int = 5):
        self.history = deque(maxlen=max_history)
        self.last_intent = None
        self.active_domain = None  # "volume" | "brightness" | None
        self.last_slots: dict = {}

    def update(self, intent_data: dict):
        intent = intent_data.get("intent")
        self.last_intent = intent
        self.history.append(intent_data)

        if intent in _VOLUME_INTENTS:
            self.active_domain = "volume"
            lv = intent_data.get("level")
            if lv is not None:
                try:
                    self.last_slots["level"] = int(float(str(lv).strip()))
                except (TypeError, ValueError):
                    pass
        elif intent in _BRIGHTNESS_INTENTS:
            self.active_domain = "brightness"
            lv = intent_data.get("level")
            if lv is not None:
                try:
                    self.last_slots["level"] = int(float(str(lv).strip()))
                except (TypeError, ValueError):
                    pass
        else:
            self.active_domain = None
            self.last_slots = {}

    def get_last_intent(self):
        return self.last_intent

    def get_history(self):
        return list(self.history)


# global instance
context = ContextManager()
