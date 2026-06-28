from __future__ import annotations

import threading


class RequestManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._active_request_id = 0

    def next_request(self) -> int:
        with self._lock:
            self._active_request_id += 1
            return self._active_request_id

    def cancel_previous(self) -> int:
        return self.next_request()

    def active_request_id(self) -> int:
        with self._lock:
            return self._active_request_id

    def is_stale(self, request_id: int) -> bool:
        with self._lock:
            return request_id != self._active_request_id


request_manager = RequestManager()
