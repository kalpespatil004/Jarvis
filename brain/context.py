# brain/context.py

from collections import deque

class ContextManager:
    def __init__(self, max_history: int = 5):
        self.history = deque(maxlen=max_history)
        self.last_intent = None

    def update(self, intent_data: dict):
        self.last_intent = intent_data.get("intent")
        self.history.append(intent_data)

    def get_last_intent(self):
        return self.last_intent

    def get_history(self):
        return list(self.history)


# global instance
context = ContextManager()