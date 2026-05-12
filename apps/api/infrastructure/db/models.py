"""
WaspNet — SQLAlchemy ORM Models
Database models for PostgreSQL persistence.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from database import Base


# ─── User Model ───────────────────────────────────────────────

class UserModel(Base):
    """Registered user account."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallets = relationship("WatchedWalletModel", back_populates="user", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRuleModel", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationModel", back_populates="user", cascade="all, delete-orphan")

    # Rate limiting
    daily_api_quota = Column(Integer, default=1000)  # Fixed window: daily quota per free user
    tier = Column(String(20), default="free")  # free, pro, enterprise


# ─── Watched Wallet Model ────────────────────────────────────

class WatchedWalletModel(Base):
    """Wallet address being monitored by a user."""
    __tablename__ = "watched_wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address = Column(String(100), nullable=False)
    network = Column(String(20), nullable=False, default="solana")
    label = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    last_balance_lamports = Column(Float, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="wallets")
    alert_rules = relationship("AlertRuleModel", back_populates="wallet", cascade="all, delete-orphan")

    # ARCH: Composite index for efficient per-user wallet lookups
    __table_args__ = (
        Index("ix_watched_wallets_user_address", "user_id", "address", unique=True),
        Index("ix_watched_wallets_network_active", "network", "is_active"),
    )


# ─── Alert Rule Model ────────────────────────────────────────

class AlertRuleModel(Base):
    """Alert rule configuration stored in database."""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("watched_wallets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    conditions = Column(JSON, nullable=False)  # List of AlertCondition dicts
    severity = Column(String(20), default="warning")  # critical, warning, info
    delivery_channels = Column(ARRAY(String), default=["in_app"])
    is_active = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=5)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="alert_rules")
    wallet = relationship("WatchedWalletModel", back_populates="alert_rules")
    notifications = relationship("NotificationModel", back_populates="alert_rule", cascade="all, delete-orphan")

    # ARCH: Index for fast active rule lookups per user
    __table_args__ = (
        Index("ix_alert_rules_user_active", "user_id", "is_active"),
        Index("ix_alert_rules_wallet_active", "wallet_id", "is_active"),
    )


# ─── Notification Model ──────────────────────────────────────

class NotificationModel(Base):
    """Delivered or pending notification log."""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(20), nullable=False)  # telegram, email, in_app, webhook
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    severity = Column(String(20), default="info")
    status = Column(String(20), default="pending")  # pending, delivered, failed, skipped
    # SEC: idempotency key prevents duplicate delivery
    idempotency_key = Column(String(100), unique=True, nullable=False)
    meta_data = Column(JSON, default={})
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="notifications")
    alert_rule = relationship("AlertRuleModel", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_status", "status"),
    )


# ─── Webhook Subscription Model ──────────────────────────────

class WebhookSubscriptionModel(Base):
    """
    Tracks active Dune SIM webhook subscriptions.
    SIM: POST /webhooks/subscribe — stored for lifecycle management.
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sim_subscription_id = Column(String(200), unique=True, nullable=False)
    wallet_address = Column(String(100), nullable=False)
    network = Column(String(20), nullable=False, default="solana")
    event_types = Column(ARRAY(String), default=["transfer"])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_webhook_subs_address", "wallet_address", "is_active"),
    )
