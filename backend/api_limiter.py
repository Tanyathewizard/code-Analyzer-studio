"""
Rate limiter and request cache to reduce API calls and avoid exhaustion.
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional
from collections import defaultdict
from backend.api_config import APIConfig

class RequestCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[float, Any]] = {}
        self.ttl = ttl_seconds
    
    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash the key for storage"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        h = self._hash_key(key)
        if h in self.cache:
            timestamp, value = self.cache[h]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[h]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache a value"""
        h = self._hash_key(key)
        self.cache[h] = (time.time(), value)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()


class RateLimiter:
    """Token bucket rate limiter per API"""
    
    def __init__(self):
        self.tokens: Dict[str, float] = defaultdict(lambda: 0.0)
        self.last_refill: Dict[str, float] = defaultdict(time.time)
    
    def wait_if_needed(self, api: str) -> None:
        """Wait if rate limit exceeded"""
        rpm = APIConfig.get_rpm_limit(api)
        tokens_per_second = rpm / 60.0
        
        now = time.time()
        time_since_refill = now - self.last_refill[api]
        
        # Refill tokens
        self.tokens[api] = min(rpm, self.tokens[api] + time_since_refill * tokens_per_second)
        self.last_refill[api] = now
        
        # If no tokens, wait
        if self.tokens[api] < 1:
            wait_time = (1 - self.tokens[api]) / tokens_per_second
            time.sleep(wait_time)
            self.tokens[api] = 0
        else:
            self.tokens[api] -= 1


# Global instances
cache = RequestCache(APIConfig.CACHE_TTL_SECONDS) if APIConfig.ENABLE_CACHE else None
rate_limiter = RateLimiter()


def get_cache_key(api: str, prompt: str, language: str = "python") -> str:
    """Generate cache key from API, prompt, and language"""
    key = f"{api}:{language}:{prompt[:500]}"  # Use first 500 chars
    return key


def should_use_cache(api: str, prompt: str, language: str = "python") -> Optional[Any]:
    """Check cache before API call"""
    if not APIConfig.ENABLE_CACHE or cache is None:
        return None
    key = get_cache_key(api, prompt, language)
    return cache.get(key)


def cache_result(api: str, prompt: str, result: Any, language: str = "python") -> None:
    """Cache successful result"""
    if not APIConfig.ENABLE_CACHE or cache is None:
        return
    key = get_cache_key(api, prompt, language)
    cache.set(key, result)


def apply_rate_limit(api: str) -> None:
    """Apply rate limiting before API call"""
    rate_limiter.wait_if_needed(api)


if __name__ == "__main__":
    # Test cache
    cache_result("openai", "test prompt", {"result": "test"})
    print("Cached:", should_use_cache("openai", "test prompt"))
    
    # Test rate limiting
    print("Testing rate limiter...")
    for i in range(3):
        apply_rate_limit("openai")
        print(f"Request {i+1} at {time.time()}")
