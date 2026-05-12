"""
ChainRadar Domain Entities — Alert Rule
Defines conditions for triggering alerts on wallet activity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConditionType(str, Enum):
    """Types of alert conditions supported."""
    BALANCE_ABOVE = "balance_above"          # Balance exceeds threshold
    BALANCE_BELOW = "balance_below"          # Balance drops below threshold
    BALANCE_CHANGE = "balance_change"        # Balance changes by percentage
    LARGE_TRANSFER = "large_transfer"        # Transfer exceeds amount
    WHALE_MOVEMENT = "whale_movement"        # Known whale address activity
    TOKEN_TRANSFER = "token_transfer"        # Specific token moved
    NEW_TOKEN = "new_token"                  # New token appears in wallet
    PROGRAM_INTERACTION = "program_interaction"  # Interaction with specific program


class Severity(str, Enum):
    """Alert severity levels for priority scoring."""
    CRITICAL = "critical"    # Immediate action needed
    WARNING = "warning"      # Attention required
    INFO = "info"            # Informational only


class DeliveryChannel(str, Enum):
    """Notification delivery channels."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


@dataclass
class AlertCondition:
    """A single condition within an alert rule."""
    condition_type: ConditionType
    threshold: float
    comparison: str = "gte"  # gte, lte, eq, gt, lt
    token_mint: Optional[str] = None  # For token-specific conditions
    program_id: Optional[str] = None  # For program interaction alerts
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """
    Domain entity for alert rules.
    A rule has one or more conditions (AND logic) and delivery preferences.
    """
    name: str
    wallet_address: str
    network: str
    conditions: List[AlertCondition]
    severity: Severity = Severity.WARNING
    delivery_channels: List[DeliveryChannel] = field(
        default_factory=lambda: [DeliveryChannel.IN_APP]
    )
    is_active: bool = True
    cooldown_minutes: int = 5  # Min time between alerts for same rule
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    id: Optional[str] = None

    @property
    def is_cooldown_active(self) -> bool:
        """Check if alert is within cooldown period."""
        if self.last_triggered_at is None:
            return False
        elapsed = (datetime.utcnow() - self.last_triggered_at).total_seconds()
        return elapsed < (self.cooldown_minutes * 60)
