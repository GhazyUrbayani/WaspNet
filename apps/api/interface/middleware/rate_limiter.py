"""
ChainRadar — Rate Limiter Middleware
Implements 4 rate limiting algorithms using Redis + Lua scripts.

Algorithms:
1. Token Bucket — per-IP rate limiting (burst allowed)
2. Leaky Bucket — outbound notification throttle (no spam)
3. Fixed Window — daily quota per free user
4. Sliding Window — per-minute API call limit
"""

import time
import structlog
from typing import Optional

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class RateLimiter:
    """Redis-backed rate limiter with 4 algorithm implementations."""

    def __init__(self, redis_url: str):
        self._redis: Optional[aioredis.Redis] = None
        self._redis_url = redis_url

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    # ─── Algorithm 1: Token Bucket ────────────────────────────
    # Per-IP rate limiting with burst capacity.
    # Tokens refill at a steady rate; burst requests consume tokens.

    async def token_bucket_check(
        self,
        key: str,
        capacity: int = 60,
        refill_rate: float = 1.0,  # tokens per second
    ) -> bool:
        """
        Token Bucket Algorithm.
        - capacity: max tokens (burst limit)
        - refill_rate: tokens added per second
        Returns True if request is allowed.
        """
        r = await self._get_redis()

        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now

        -- Refill tokens based on elapsed time
        local elapsed = now - last_refill
        local new_tokens = math.min(capacity, tokens + (elapsed * refill_rate))

        if new_tokens >= 1 then
            -- Consume one token
            redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 1)
            return 1
        else
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 1)
            return 0
        end
        """

        result = await r.eval(lua_script, 1, f"rl:tb:{key}", capacity, refill_rate, time.time())
        return bool(result)

    # ─── Algorithm 2: Leaky Bucket ────────────────────────────
    # Outbound notification throttle — constant drain rate, no spam.

    async def leaky_bucket_check(
        self,
        key: str,
        capacity: int = 10,
        leak_rate: float = 0.5,  # requests drained per second
    ) -> bool:
        """
        Leaky Bucket Algorithm.
        - capacity: max queue size
        - leak_rate: requests processed per second
        Ensures constant output rate regardless of burst input.
        """
        r = await self._get_redis()

        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local leak_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'water', 'last_leak')
        local water = tonumber(bucket[1]) or 0
        local last_leak = tonumber(bucket[2]) or now

        -- Leak water based on elapsed time
        local elapsed = now - last_leak
        local leaked = elapsed * leak_rate
        water = math.max(0, water - leaked)

        if water < capacity then
            -- Add one drop
            redis.call('HMSET', key, 'water', water + 1, 'last_leak', now)
            redis.call('EXPIRE', key, math.ceil(capacity / leak_rate) + 1)
            return 1
        else
            redis.call('HMSET', key, 'water', water, 'last_leak', now)
            redis.call('EXPIRE', key, math.ceil(capacity / leak_rate) + 1)
            return 0
        end
        """

        result = await r.eval(lua_script, 1, f"rl:lb:{key}", capacity, leak_rate, time.time())
        return bool(result)

    # ─── Algorithm 3: Fixed Window ────────────────────────────
    # Daily quota per free user — simple counter with expiry.

    async def fixed_window_check(
        self,
        key: str,
        limit: int = 1000,
        window_seconds: int = 86400,  # 24 hours
    ) -> bool:
        """
        Fixed Window Algorithm.
        - limit: max requests in window
        - window_seconds: window duration
        Simple but has boundary burst problem.
        """
        r = await self._get_redis()
        window_key = f"rl:fw:{key}:{int(time.time() / window_seconds)}"

        count = await r.incr(window_key)
        if count == 1:
            await r.expire(window_key, window_seconds)

        return count <= limit

    # ─── Algorithm 4: Sliding Window ──────────────────────────
    # Per-minute API call limit — smoothest rate limiting.

    async def sliding_window_check(
        self,
        key: str,
        limit: int = 60,
        window_seconds: int = 60,
    ) -> bool:
        """
        Sliding Window Algorithm (log-based).
        - limit: max requests in sliding window
        - window_seconds: window duration
        Most accurate but slightly more expensive.
        """
        r = await self._get_redis()
        now = time.time()
        window_start = now - window_seconds
        sw_key = f"rl:sw:{key}"

        pipe = r.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(sw_key, 0, window_start)
        # Count current entries
        pipe.zcard(sw_key)
        # Add current request
        pipe.zadd(sw_key, {str(now): now})
        # Set expiry
        pipe.expire(sw_key, window_seconds + 1)

        results = await pipe.execute()
        count = results[1]

        if count >= limit:
            # Remove the entry we just added
            await r.zrem(sw_key, str(now))
            return False
        return True

    async def close(self):
        if self._redis:
            await self._redis.aclose()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that applies rate limiting to all requests.
    Uses Token Bucket for per-IP and Sliding Window for per-user.
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.limiter = rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Algorithm 1: Token Bucket — per-IP (60 req/min with burst)
        allowed = await self.limiter.token_bucket_check(
            key=f"ip:{client_ip}",
            capacity=60,
            refill_rate=1.0,
        )

        if not allowed:
            logger.warning("Rate limit exceeded (IP)", ip=client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Policy"] = "token-bucket"
        return response


# Singleton
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(settings.redis_url)
    return _rate_limiter
