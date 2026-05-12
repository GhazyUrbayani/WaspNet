"""
WaspNet Domain Entities — Notification
Represents a delivered or pending alert notification.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class NotificationStatus(str, Enum):
    """Delivery status of a notification."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"  # Deduplicated or cooldown


@dataclass
class Notification:
    """
    Domain entity for alert notifications.
    Each notification has an idempotency key to prevent duplicate delivery.
    """
    alert_rule_id: str
    user_id: str
    channel: str  # telegram, email, in_app, webhook
    title: str
    body: str
    severity: str
    status: NotificationStatus = NotificationStatus.PENDING
    # SEC: idempotency key prevents duplicate notifications
    idempotency_key: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    delivered_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None

    def mark_delivered(self):
        """Mark notification as successfully delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark notification as failed with error detail."""
        self.status = NotificationStatus.FAILED
        self.metadata["error"] = error
