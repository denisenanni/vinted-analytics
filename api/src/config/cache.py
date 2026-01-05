"""
Simple in-memory cache for API responses.
Cache duration: 5 hours (data refreshes every 24h via scraper)
"""
from functools import wraps
from typing import Any, Callable
import time
import hashlib
import json

# In-memory cache storage
_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL = 5 * 60 * 60  # 5 hours in seconds


def cache_response(ttl: int = CACHE_TTL):
    """
    Decorator to cache API endpoint responses.

    Args:
        ttl: Time to live in seconds (default: 5 hours)

    Usage:
        @router.get("/endpoint")
        @cache_response()
        async def endpoint(param: str):
            return {"data": "value"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            # Skip 'self' or 'cls' from args if present
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args

            key_data = {
                "func": func.__name__,
                "args": str(cache_args),
                "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
            }
            key_str = json.dumps(key_data, sort_keys=True)
            cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # Check if cached and not expired
            if cache_key in _cache:
                cached_data, expire_time = _cache[cache_key]
                if time.time() < expire_time:
                    return cached_data
                else:
                    # Expired, remove from cache
                    del _cache[cache_key]

            # Execute function and cache result
            result = await func(*args, **kwargs)
            _cache[cache_key] = (result, time.time() + ttl)

            return result

        return wrapper
    return decorator


def clear_cache():
    """Clear all cached responses. Useful for testing or manual cache invalidation."""
    _cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    now = time.time()
    active_entries = sum(1 for _, expire_time in _cache.values() if expire_time > now)
    expired_entries = len(_cache) - active_entries

    return {
        "total_entries": len(_cache),
        "active_entries": active_entries,
        "expired_entries": expired_entries,
        "ttl_seconds": CACHE_TTL
    }
