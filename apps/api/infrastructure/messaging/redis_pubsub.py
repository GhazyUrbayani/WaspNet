"""
WaspNet — Redis Pub/Sub for Event-Driven Architecture
ARCH: SIM webhook → Redis pub/sub → notification workers.
"""

import json
import structlog
from typing import Any, AsyncGenerator, Callable, Dict

import redis.asyncio as aioredis

from config import get_settings

settings = get_settings()
logger = structlog.get_logger()

# Channel names
CHANNEL_WALLET_EVENT = "waspnet:events:wallet"
CHANNEL_ALERT_TRIGGER = "waspnet:events:alert"
CHANNEL_NOTIFICATION = "waspnet:events:notification"


class RedisPubSub:
    """
    Redis pub/sub for event-driven message passing.
    ARCH: Decouples webhook receiver from alert evaluation and notification delivery.
    """

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def publish(self, channel: str, data: Dict[str, Any]) -> int:
        """Publish an event to a channel. Returns subscriber count."""
        r = await self._get_redis()
        message = json.dumps(data, default=str)
        count = await r.publish(channel, message)
        logger.info("Event published", channel=channel, subscribers=count)
        return count

    async def subscribe(self, *channels: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to channels and yield events as they arrive."""
        r = await self._get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(*channels)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        data["_channel"] = message["channel"]
                        yield data
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON in pub/sub", channel=message["channel"])
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()

    async def publish_wallet_event(self, wallet_address: str, event_type: str, event_data: Dict) -> int:
        """Publish a wallet event from SIM webhook."""
        return await self.publish(CHANNEL_WALLET_EVENT, {
            "wallet_address": wallet_address,
            "event_type": event_type,
            "data": event_data,
        })

    async def publish_alert_trigger(self, alert_rule_id: str, wallet_address: str, details: Dict) -> int:
        """Publish an alert trigger for notification delivery."""
        return await self.publish(CHANNEL_ALERT_TRIGGER, {
            "alert_rule_id": alert_rule_id,
            "wallet_address": wallet_address,
            "details": details,
        })

    async def close(self):
        if self._redis:
            await self._redis.aclose()


# Singleton
_pubsub = None

def get_pubsub() -> RedisPubSub:
    global _pubsub
    if _pubsub is None:
        _pubsub = RedisPubSub()
    return _pubsub
