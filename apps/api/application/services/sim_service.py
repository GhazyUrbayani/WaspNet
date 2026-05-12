"""
ChainRadar — SIM Service
Orchestrates Dune SIM API calls with caching layer.
SIM: All data reads go through this service → cache → SIM API.
"""

import structlog
from typing import Any, Dict

from application.services.cache_service import get_cache_service
from infrastructure.sim.sim_client import get_sim_client

logger = structlog.get_logger()


class SIMService:
    """
    Orchestration layer between SIM API client and cache.
    ARCH: Stale-while-revalidate pattern — serve cache, refresh in background.
    """

    def __init__(self):
        self._client = get_sim_client()
        self._cache = get_cache_service()

    async def get_wallet_balances(self, address: str) -> Dict[str, Any]:
        """
        SIM: GET /v1/solana/balances/{address}
        Returns cached balance if available, else fetches from SIM.
        """
        # Check cache first
        cached = await self._cache.get("balance", address)
        if cached:
            return cached

        # Fetch from SIM
        data = await self._client.get_solana_balances(address)
        await self._cache.set("balance", address, data)
        logger.info("SIM balance fetched", address=address[:8] + "...")
        return data

    async def get_wallet_transactions(
        self, address: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        SIM: GET /v1/solana/transactions/{address}
        Cached for 5 minutes.
        """
        cache_key = f"{address}:{limit}:{offset}"
        cached = await self._cache.get("transactions", cache_key)
        if cached:
            return cached

        data = await self._client.get_solana_transactions(address, limit, offset)
        await self._cache.set("transactions", cache_key, data)
        logger.info("SIM transactions fetched", address=address[:8] + "...", count=limit)
        return data

    async def get_evm_activity(self, address: str) -> Dict[str, Any]:
        """
        SIM: GET /v1/evm/activity/{address}
        Cross-chain footprint for EVM addresses.
        """
        cached = await self._cache.get("evm_activity", address)
        if cached:
            return cached

        data = await self._client.get_evm_activity(address)
        await self._cache.set("evm_activity", address, data)
        logger.info("SIM EVM activity fetched", address=address[:8] + "...")
        return data

    async def subscribe_wallet_webhook(
        self, address: str, callback_url: str
    ) -> Dict[str, Any]:
        """
        SIM: POST /webhooks/subscribe
        Subscribe to real-time push events for wallet monitoring.
        """
        result = await self._client.subscribe_webhook(address, callback_url)
        logger.info(
            "SIM webhook subscribed",
            address=address[:8] + "...",
            subscription_id=result.get("id", "unknown"),
        )
        return result

    async def get_wallet_overview(self, address: str) -> Dict[str, Any]:
        """
        Composite call — get balances + recent transactions in parallel.
        ARCH: Single call for dashboard view, reduces frontend requests.
        """
        import asyncio
        balances_task = asyncio.create_task(self.get_wallet_balances(address))
        txns_task = asyncio.create_task(self.get_wallet_transactions(address, limit=10))

        balances, transactions = await asyncio.gather(
            balances_task, txns_task, return_exceptions=True
        )

        return {
            "address": address,
            "balances": balances if not isinstance(balances, Exception) else {"error": str(balances)},
            "transactions": transactions if not isinstance(transactions, Exception) else {"error": str(transactions)},
        }


# Singleton
_sim_service = None

def get_sim_service() -> SIMService:
    global _sim_service
    if _sim_service is None:
        _sim_service = SIMService()
    return _sim_service
