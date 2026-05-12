"""
WaspNet — Repository Interfaces (Abstract Base Classes)
Domain-layer contracts for data access. Infrastructure layer implements these.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID


class WalletRepository(ABC):
    """Interface for wallet data access."""

    @abstractmethod
    async def create(self, user_id: UUID, address: str, network: str, label: Optional[str] = None):
        """Add a wallet to the user's watchlist."""
        ...

    @abstractmethod
    async def get_by_id(self, wallet_id: UUID):
        """Get wallet by ID."""
        ...

    @abstractmethod
    async def get_by_address(self, address: str, user_id: UUID):
        """Get wallet by address for a specific user."""
        ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID, active_only: bool = True):
        """List all wallets for a user."""
        ...

    @abstractmethod
    async def update(self, wallet_id: UUID, **kwargs):
        """Update wallet fields."""
        ...

    @abstractmethod
    async def delete(self, wallet_id: UUID):
        """Remove wallet from watchlist."""
        ...

    @abstractmethod
    async def get_all_active_addresses(self) -> List[str]:
        """Get all actively monitored addresses across all users."""
        ...


class AlertRuleRepository(ABC):
    """Interface for alert rule data access."""

    @abstractmethod
    async def create(self, rule_data: dict):
        """Create a new alert rule."""
        ...

    @abstractmethod
    async def get_by_id(self, rule_id: UUID):
        """Get alert rule by ID."""
        ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID, active_only: bool = True):
        """List all alert rules for a user."""
        ...

    @abstractmethod
    async def list_by_wallet(self, wallet_address: str, active_only: bool = True):
        """List all active rules for a wallet address — used by webhook handler."""
        ...

    @abstractmethod
    async def update(self, rule_id: UUID, **kwargs):
        """Update alert rule."""
        ...

    @abstractmethod
    async def delete(self, rule_id: UUID):
        """Delete alert rule."""
        ...

    @abstractmethod
    async def mark_triggered(self, rule_id: UUID):
        """Update last_triggered_at and increment trigger_count."""
        ...
