"""
WaspNet — Webhook Router
SIM: Receives real-time push events from Dune SIM webhooks.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from infrastructure.messaging.webhook_handler import get_webhook_handler

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookResponse(BaseModel):
    status: str
    event_id: Optional[str] = None
    reason: Optional[str] = None


@router.post("/sim", response_model=WebhookResponse)
async def receive_sim_webhook(
    request: Request,
    x_sim_signature: Optional[str] = Header(None),
):
    """
    SIM: Webhook callback endpoint.
    Dune SIM sends POST requests here when wallet events occur.

    Flow: SIM → this endpoint → webhook_handler → Redis pub/sub → alert workers
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    handler = get_webhook_handler()
    result = await handler.handle_sim_event(
        payload=payload,
        signature=x_sim_signature or "",
    )

    return WebhookResponse(**result)


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {"status": "ready", "endpoint": "/webhooks/sim"}
