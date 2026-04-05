import time
import asyncio
from collections import defaultdict
from typing import Optional, Tuple

ROUTE_LIMITS = {
    "login": (5, 60),
    "register": (3, 60),
    "password_reset": (3, 60),
    "create_payment_intent": (10, 60),
    "create_appointment": (20, 60),
    "upload_file": (10, 60),
    "report_creation": (10, 60),
    "exceptional_access_request": (5, 60),
    "default": (100, 60),
}

_rate_limit_store: dict = defaultdict(lambda: defaultdict(list))
_lock = asyncio.Lock()


class RateLimiter:

    @classmethod
    async def is_allowed(
        cls,
        actor_id: Optional[str],
        route_key: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        key = actor_id or ip_address or "anonymous"
        limit_config = ROUTE_LIMITS.get(route_key, ROUTE_LIMITS["default"])
        max_requests, window_seconds = limit_config

        now = time.time()
        cutoff = now - window_seconds

        async with _lock:
            actor_entries = _rate_limit_store[route_key][key]
            actor_entries = [t for t in actor_entries if t > cutoff]

            if len(actor_entries) >= max_requests:
                oldest = actor_entries[0]
                retry_after = int(oldest + window_seconds - now)
                return False, "throttle", max(retry_after, 1)

            actor_entries.append(now)
            _rate_limit_store[route_key][key] = actor_entries
            return True, "allowed", None

    @classmethod
    async def clear_expired(cls, max_age_seconds: int = 3600):
        now = time.time()
        cutoff = now - max_age_seconds

        async with _lock:
            for route_key in list(_rate_limit_store.keys()):
                for actor_id in list(_rate_limit_store[route_key].keys()):
                    _rate_limit_store[route_key][actor_id] = [
                        t for t in _rate_limit_store[route_key][actor_id]
                        if t > cutoff
                    ]
                    if not _rate_limit_store[route_key][actor_id]:
                        del _rate_limit_store[route_key][actor_id]
                if not _rate_limit_store[route_key]:
                    del _rate_limit_store[route_key]

    @classmethod
    def get_limits_config(cls) -> dict:
        return dict(ROUTE_LIMITS)
