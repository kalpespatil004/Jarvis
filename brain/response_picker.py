import json
import random
import os

_RESPONSES = None


def get_response(intent: str, value: str = "") -> str:
    global _RESPONSES

    if _RESPONSES is None:
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "responses.json"
        )
   
        with open(path, "r", encoding="utf-8") as f:
            _RESPONSES = json.load(f)

    choices = _RESPONSES.get(intent) or _RESPONSES.get("fallback")
    template = random.choice(choices)

    return template.format(value=value)

