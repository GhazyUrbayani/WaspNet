"""
ChainRadar — Redis Cache Service
Caching layer for SIM API responses with TTL strategy.
ARCH: balances cached 30s, transactions 5min — as specified.
"""

import json
import structlog
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from config import get_settings

settings = get_settings()
logger = structlog.get_logger()

# Cache TTL strategy (in seconds)
CACHE_TTL = {
    "balance": 30,         # 30s — balances change frequently
    "transactions": 300,   # 5min — history changes less often
    "evm_activity": 300,   # 5min — cross-chain activity
    "webhook_sub": 3600,   # 1hr — subscription metadata
}


class CacheService:
    """
    Redis cache wrapper with namespace isolation and TTL management.
    ARCH: All SIM API responses are cached to reduce API calls and latency.
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _key(self, namespace: str, identifier: str) -> str:
        """Generate namespaced cache key."""
        return f"chainradar:{namespace}:{identifier}"

    async def get(self, namespace: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Get cached data by namespace and identifier."""
        r = await self._get_redis()
        key = self._key(namespace, identifier)
        data = await r.get(key)
        if data:
            logger.debug("Cache HIT", namespace=namespace, key=identifier)
            return json.loads(data)
        logger.debug("Cache MISS", namespace=namespace, key=identifier)
        return None

    async def set(
        self,
        namespace: str,
        identifier: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set cached data with TTL."""
        r = await self._get_redis()
        key = self._key(namespace, identifier)
        ttl = ttl or CACHE_TTL.get(namespace, 60)
        await r.setex(key, ttl, json.dumps(data, default=str))
        logger.debug("Cache SET", namespace=namespace, key=identifier, ttl=ttl)

    async def invalidate(self, namespace: str, identifier: str) -> None:
        """Remove specific cache entry."""
        r = await self._get_redis()
        key = self._key(namespace, identifier)
        await r.delete(key)

    async def invalidate_namespace(self, namespace: str) -> None:
        """Remove all entries in a namespace."""
        r = await self._get_redis()
        pattern = self._key(namespace, "*")
        keys = []
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await r.delete(*keys)

    async def close(self):
        if self._redis:
            await self._redis.aclose()


# Singleton
_cache: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
