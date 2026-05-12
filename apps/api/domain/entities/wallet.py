"""
WaspNet Domain Entities — Wallet
Core wallet entity for tracking monitored addresses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Network(str, Enum):
    """Supported blockchain networks."""
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    BASE = "base"


@dataclass
class Wallet:
    """
    Domain entity representing a monitored wallet address.
    Network-agnostic — supports both Solana and EVM chains.
    """
    address: str
    network: Network
    label: Optional[str] = None
    user_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None

    def __post_init__(self):
        """Validate wallet address format."""
        if self.network == Network.SOLANA:
            self._validate_solana_address()
        else:
            self._validate_evm_address()

    def _validate_solana_address(self):
        """SEC: Validate Solana address is valid base58."""
        import base58
        try:
            decoded = base58.b58decode(self.address)
            if len(decoded) != 32:
                raise ValueError(f"Invalid Solana address length: {len(decoded)}")
        except Exception as e:
            raise ValueError(f"Invalid Solana address: {self.address}") from e

    def _validate_evm_address(self):
        """SEC: Validate EVM address format (0x + 40 hex chars)."""
        import re
        if not re.match(r"^0x[a-fA-F0-9]{40}$", self.address):
            raise ValueError(f"Invalid EVM address: {self.address}")
