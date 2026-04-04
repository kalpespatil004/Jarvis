# brain/events.py

_event_listeners = {}

def register_event(event_name: str, callback):
    if event_name not in _event_listeners:
        _event_listeners[event_name] = []
    _event_listeners[event_name].append(callback)


def trigger_event(event_name: str, data=None):
    listeners = _event_listeners.get(event_name, [])
    for callback in listeners:
        try:
            callback(data)
        except Exception as e:
            print(f"[EVENT ERROR] {e}")