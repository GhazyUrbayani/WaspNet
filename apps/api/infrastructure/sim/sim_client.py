"""
WaspNet — Dune SIM API Client
Async HTTP client with circuit breaker, retry backoff, and timeout.

SIM: All 4 endpoint types used:
  - GET /v1/solana/balances/{address}
  - GET /v1/solana/transactions/{address}
  - GET /v1/evm/activity/{address}
  - POST /webhooks/subscribe
"""

import asyncio
import structlog
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from infrastructure.sim.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

settings = get_settings()
logger = structlog.get_logger()


class SIMClientError(Exception):
    """Base error for SIM API client."""
    pass


class SIMRateLimitError(SIMClientError):
    """Raised when SIM API returns 429."""
    pass


class SIMClient:
    """
    Async Dune SIM API client.
    SIM: Core data layer — all wallet data flows through this client.

    Features:
    - 5s timeout per request
    - Exponential backoff (3 retries)
    - Circuit breaker pattern
    - API key from env (never logged)
    """

    def __init__(self):
        self._base_url = settings.sim_base_url
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
        )
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "X-Sim-Api-Key": settings.sim_api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "WaspNet/1.0",
                },
                timeout=httpx.Timeout(5.0),  # SIM: 5s timeout as specified
            )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        max_retries: int = 3,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry.
        ARCH: Retries on 5xx and timeout, NOT on 4xx (client errors).
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                result = await self._circuit_breaker.call(
                    self._do_request, method, path, **kwargs
                )
                return result
            except CircuitBreakerOpenError:
                logger.warning("SIM circuit breaker open", path=path)
                raise SIMClientError("SIM API circuit breaker is open — service degraded")
            except SIMRateLimitError:
                # Don't retry on rate limit — bubble up immediately
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    wait = 2 ** attempt
                    logger.warning(
                        "SIM request retry",
                        path=path, attempt=attempt + 1, wait=wait,
                        error=str(e),
                    )
                    await asyncio.sleep(wait)
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_exception = e
                    if attempt < max_retries:
                        wait = 2 ** attempt
                        await asyncio.sleep(wait)
                        continue
                raise SIMClientError(f"SIM API error: {e.response.status_code}")

        raise SIMClientError(f"SIM API request failed after {max_retries} retries: {last_exception}")

    async def _do_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute a single HTTP request."""
        client = await self._get_client()
        response = await client.request(method, path, **kwargs)

        if response.status_code == 429:
            raise SIMRateLimitError("SIM API rate limit exceeded")

        response.raise_for_status()

        # SEC: Log request without API key
        logger.info("SIM request", method=method, path=path, status=response.status_code)
        return response.json()

    # ─── Public API Methods ───────────────────────────────────

    async def get_solana_balances(self, address: str) -> Dict[str, Any]:
        """
        SIM: GET /v1/solana/balances/{address}
        Returns SOL balance + all token balances for the address.
        """
        return await self._request_with_retry("GET", f"/solana/balances/{address}")

    async def get_solana_transactions(
        self,
        address: str,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        SIM: GET /v1/solana/transactions/{address}
        Returns recent transactions for the address.
        """
        return await self._request_with_retry(
            "GET",
            f"/solana/transactions/{address}",
            params={"limit": limit, "offset": offset},
        )

    async def get_evm_activity(self, address: str) -> Dict[str, Any]:
        """
        SIM: GET /v1/evm/activity/{address}
        Returns cross-chain activity for EVM-compatible address.
        """
        return await self._request_with_retry("GET", f"/evm/activity/{address}")

    async def subscribe_webhook(
        self,
        wallet_address: str,
        callback_url: str,
        event_types: List[str] = None,
    ) -> Dict[str, Any]:
        """
        SIM: POST /webhooks/subscribe
        Subscribe to real-time push events for a wallet address.
        This is the KILLER differentiator for WaspNet.
        """
        if event_types is None:
            event_types = ["transfer", "token_transfer", "program_interaction"]

        payload = {
            "address": wallet_address,
            "callback_url": callback_url,
            "event_types": event_types,
        }
        return await self._request_with_retry("POST", "/webhooks/subscribe", json=payload)

    async def unsubscribe_webhook(self, subscription_id: str) -> Dict[str, Any]:
        """Remove a webhook subscription."""
        return await self._request_with_retry("DELETE", f"/webhooks/{subscription_id}")

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton instance
_sim_client: Optional[SIMClient] = None


def get_sim_client() -> SIMClient:
    """Get or create the SIM client singleton."""
    global _sim_client
    if _sim_client is None:
        _sim_client = SIMClient()
    return _sim_client
