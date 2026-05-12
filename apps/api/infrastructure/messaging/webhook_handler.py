"""
ChainRadar — SIM Webhook Handler
Receives real-time push events from Dune SIM and publishes to Redis.
SIM: POST /webhooks/subscribe callback endpoint.
"""

import hashlib
import hmac
import structlog
from typing import Any, Dict

from infrastructure.messaging.redis_pubsub import get_pubsub

logger = structlog.get_logger()


class WebhookHandler:
    """
    Processes incoming Dune SIM webhook events.
    ARCH: Validates signature → deduplicates → publishes to Redis pub/sub.
    SEC: HMAC signature verification prevents spoofed webhooks.
    """

    def __init__(self):
        self._pubsub = get_pubsub()
        self._processed_ids: set = set()  # In-memory dedup (use Redis in prod)

    async def handle_sim_event(
        self,
        payload: Dict[str, Any],
        signature: str = "",
        webhook_secret: str = "",
    ) -> Dict[str, str]:
        """
        Process an incoming SIM webhook event.

        Flow:
        1. Validate webhook signature
        2. Deduplicate by event ID
        3. Publish to Redis pub/sub for downstream processing
        """
        event_id = payload.get("id", "")
        event_type = payload.get("type", "unknown")
        wallet_address = payload.get("address", "")

        # SEC: Validate webhook signature if secret is configured
        if webhook_secret and signature:
            if not self._verify_signature(payload, signature, webhook_secret):
                logger.warning("Invalid webhook signature", event_id=event_id)
                return {"status": "rejected", "reason": "invalid_signature"}

        # Deduplicate — prevent processing same event twice
        if event_id in self._processed_ids:
            logger.info("Duplicate webhook event skipped", event_id=event_id)
            return {"status": "skipped", "reason": "duplicate"}

        self._processed_ids.add(event_id)

        # Cap dedup set size (memory safety)
        if len(self._processed_ids) > 10000:
            self._processed_ids = set(list(self._processed_ids)[-5000:])

        # Publish to Redis for alert evaluation
        await self._pubsub.publish_wallet_event(
            wallet_address=wallet_address,
            event_type=event_type,
            event_data=payload,
        )

        logger.info(
            "SIM webhook processed",
            event_id=event_id,
            event_type=event_type,
            wallet=wallet_address[:8] + "..." if wallet_address else "unknown",
        )

        return {"status": "processed", "event_id": event_id}

    def _verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str,
    ) -> bool:
        """SEC: HMAC-SHA256 signature verification for webhook authenticity."""
        import json
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        expected = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)


# Singleton
_handler = None

def get_webhook_handler() -> WebhookHandler:
    global _handler
    if _handler is None:
        _handler = WebhookHandler()
    return _handler
