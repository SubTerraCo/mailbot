"""Short-lived OAuth CSRF state -> account_id (in-memory)."""

from __future__ import annotations

import secrets
import threading
import time

_LOCK = threading.Lock()
_STORE: dict[str, tuple[str, float]] = {}
_TTL_SEC = 600.0


def issue_state(account_id: str) -> str:
    state = secrets.token_urlsafe(32)
    now = time.monotonic()
    with _LOCK:
        _prune_unlocked(now)
        _STORE[state] = (account_id, now)
    return state


def consume_state(state: str | None) -> str | None:
    if not state:
        return None
    now = time.monotonic()
    with _LOCK:
        _prune_unlocked(now)
        row = _STORE.pop(state, None)
    if not row:
        return None
    account_id, issued = row
    if now - issued > _TTL_SEC:
        return None
    return account_id


def _prune_unlocked(now: float) -> None:
    dead = [k for k, (_, t) in _STORE.items() if now - t > _TTL_SEC]
    for k in dead:
        _STORE.pop(k, None)
