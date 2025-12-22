# brain/intent_engine.py

def detect_intent(text: str) -> dict:
    text = text.lower()

    if "time" in text:
        return {"intent": "get_time"}

    if "open" in text:
        return {"intent": "open_app", "app": text.replace("open", "").strip()}

    return {"intent": "chat", "text": text}
