"""
ChainRadar — SSE Stream Router
Server-Sent Events for real-time in-app notifications.
"""

import asyncio
import json
import structlog

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from infrastructure.db.models import UserModel
from infrastructure.messaging.redis_pubsub import (
    CHANNEL_ALERT_TRIGGER,
    CHANNEL_NOTIFICATION,
    get_pubsub,
)
from interface.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/stream", tags=["SSE Stream"])
logger = structlog.get_logger()


@router.get("/events")
async def stream_events(
    request: Request,
    user: UserModel = Depends(get_current_user),
):
    """
    SSE endpoint — streams real-time alert notifications to the frontend.
    ARCH: Uses Redis pub/sub to push events to connected clients.
    """

    async def event_generator():
        pubsub = get_pubsub()
        user_id = str(user.id)

        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'user_id': user_id})}\n\n"

        try:
            async for event in pubsub.subscribe(CHANNEL_ALERT_TRIGGER, CHANNEL_NOTIFICATION):
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Filter events for this user
                event_user = event.get("user_id", "")
                if event_user and event_user != user_id:
                    continue

                channel = event.get("_channel", "")
                event_type = "alert" if "alert" in channel else "notification"

                yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled", user_id=user_id)
        except Exception as e:
            logger.error("SSE stream error", user_id=user_id, error=str(e))
            yield f"event: error\ndata: {json.dumps({'error': 'Stream error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/ping")
async def ping():
    """SSE keepalive test endpoint."""
    return {"status": "pong"}
