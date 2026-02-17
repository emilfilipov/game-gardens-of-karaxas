from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from math import ceil
from threading import RLock
import time

from fastapi import HTTPException, Request, status

from app.core.config import settings


@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    window_seconds: int
    lockout_seconds: int


AUTH_IP_RULE = RateLimitRule(
    limit=max(1, settings.auth_rate_limit_max_attempts_per_ip),
    window_seconds=max(1, settings.auth_rate_limit_window_seconds),
    lockout_seconds=max(1, settings.auth_rate_limit_lockout_seconds),
)
AUTH_ACCOUNT_RULE = RateLimitRule(
    limit=max(1, settings.auth_rate_limit_max_attempts_per_account),
    window_seconds=max(1, settings.auth_rate_limit_window_seconds),
    lockout_seconds=max(1, settings.auth_rate_limit_lockout_seconds),
)
CHAT_IP_RULE = RateLimitRule(
    limit=max(1, settings.chat_write_rate_limit_max_per_ip),
    window_seconds=max(1, settings.chat_write_rate_limit_window_seconds),
    lockout_seconds=max(1, settings.chat_write_rate_limit_lockout_seconds),
)
CHAT_ACCOUNT_RULE = RateLimitRule(
    limit=max(1, settings.chat_write_rate_limit_max_per_account),
    window_seconds=max(1, settings.chat_write_rate_limit_window_seconds),
    lockout_seconds=max(1, settings.chat_write_rate_limit_lockout_seconds),
)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._blocked_until: dict[tuple[str, str], float] = {}
        self._lock = RLock()

    def _prune(self, key: tuple[str, str], now: float, window_seconds: int) -> None:
        entries = self._events.get(key)
        if entries is None:
            return
        cutoff = now - float(window_seconds)
        while entries and entries[0] < cutoff:
            entries.popleft()
        if not entries:
            self._events.pop(key, None)

    def check(self, bucket: str, subject: str, rule: RateLimitRule) -> tuple[bool, int]:
        if not settings.request_rate_limit_enabled:
            return True, 0
        now = time.time()
        key = (bucket, subject)
        with self._lock:
            blocked = self._blocked_until.get(key, 0.0)
            if blocked > now:
                return False, max(1, int(ceil(blocked - now)))
            self._prune(key, now, rule.window_seconds)
            entries = self._events.get(key, deque())
            if len(entries) >= rule.limit:
                until = now + float(rule.lockout_seconds)
                self._blocked_until[key] = until
                self._events.pop(key, None)
                return False, rule.lockout_seconds
            return True, 0

    def record_failure(self, bucket: str, subject: str, rule: RateLimitRule) -> None:
        if not settings.request_rate_limit_enabled:
            return
        now = time.time()
        key = (bucket, subject)
        with self._lock:
            self._prune(key, now, rule.window_seconds)
            entries = self._events[key]
            entries.append(now)
            if len(entries) >= rule.limit:
                self._blocked_until[key] = now + float(rule.lockout_seconds)
                self._events.pop(key, None)

    def reset(self, bucket: str, subject: str) -> None:
        key = (bucket, subject)
        with self._lock:
            self._events.pop(key, None)
            self._blocked_until.pop(key, None)

    def stats(self) -> dict[str, int]:
        with self._lock:
            active_event_keys = len(self._events)
            blocked_keys = sum(1 for until in self._blocked_until.values() if until > time.time())
        return {
            "tracked_keys": active_event_keys,
            "blocked_keys": blocked_keys,
        }


rate_limiter = InMemoryRateLimiter()


def request_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def ensure_not_rate_limited(bucket: str, subject: str, rule: RateLimitRule) -> None:
    allowed, retry_after = rate_limiter.check(bucket, subject, rule)
    if allowed:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "message": "Too many requests. Please try again later.",
            "code": "rate_limit_exceeded",
            "retry_after_seconds": retry_after,
        },
    )
