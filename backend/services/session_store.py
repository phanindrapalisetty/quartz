import secrets
import time
from typing import Optional, Dict, Any


class SessionStore:
    """
    In-memory session store. Swap for Redis in production
    by implementing the same interface backed by redis-py.
    """

    def __init__(self, ttl_seconds: int = 3600 * 24 * 7):  # 7 days — matches cookie TTL
        self._store: Dict[str, Dict] = {}
        self.ttl = ttl_seconds

    def create(self, data: Dict[str, Any]) -> str:
        session_id = secrets.token_urlsafe(32)
        self._store[session_id] = {"data": data, "last_accessed": time.time()}
        return session_id

    def get(self, session_id: str) -> Optional[Dict]:
        entry = self._store.get(session_id)
        if not entry:
            return None
        if time.time() - entry["last_accessed"] > self.ttl:
            self._store.pop(session_id, None)
            return None
        entry["last_accessed"] = time.time()  # sliding window — reset on each use
        return entry["data"]

    def update(self, session_id: str, data: Dict[str, Any]) -> bool:
        if session_id not in self._store:
            return False
        self._store[session_id]["data"].update(data)
        return True

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)


# Singleton — one store per process
session_store = SessionStore()
