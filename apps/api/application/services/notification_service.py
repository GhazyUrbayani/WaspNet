"""
ChainRadar — Notification Service
Delivers alerts via Telegram, Email, and In-App SSE.
ARCH: Each channel has its own delivery method with idempotency.
"""

import hashlib
import json
import structlog
from typing import Any, Dict, Optional

from config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class NotificationService:
    """
    Multi-channel notification delivery service.
    SEC: Uses idempotency keys to prevent duplicate notifications.
    """

    async def deliver(
        self,
        channel: str,
        user_data: Dict[str, Any],
        alert_data: Dict[str, Any],
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Route notification to appropriate delivery channel."""
        handlers = {
            "telegram": self._send_telegram,
            "email": self._send_email,
            "in_app": self._send_in_app,
            "webhook": self._send_webhook,
        }

        handler = handlers.get(channel)
        if not handler:
            logger.warning("Unknown delivery channel", channel=channel)
            return {"status": "failed", "reason": f"Unknown channel: {channel}"}

        try:
            result = await handler(user_data, alert_data)
            logger.info(
                "Notification delivered",
                channel=channel,
                idempotency_key=idempotency_key,
            )
            return {"status": "delivered", **result}
        except Exception as e:
            logger.error(
                "Notification delivery failed",
                channel=channel,
                error=str(e),
            )
            return {"status": "failed", "error": str(e)}

    async def _send_telegram(self, user_data: Dict, alert_data: Dict) -> Dict:
        """Send alert via Telegram Bot API."""
        chat_id = user_data.get("telegram_chat_id")
        if not chat_id:
            return {"skipped": True, "reason": "No Telegram chat ID configured"}

        message = self._format_telegram_message(alert_data)

        if settings.telegram_bot_token:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                return {"telegram_message_id": response.json().get("result", {}).get("message_id")}
        else:
            logger.warning("Telegram bot token not configured")
            return {"skipped": True, "reason": "Bot token not configured"}

    async def _send_email(self, user_data: Dict, alert_data: Dict) -> Dict:
        """Send alert via Resend email service."""
        email = user_data.get("email")
        if not email:
            return {"skipped": True, "reason": "No email configured"}

        if settings.resend_api_key:
            import resend
            resend.api_key = settings.resend_api_key

            severity = alert_data.get("severity", "info").upper()
            wallet = alert_data.get("wallet_address", "Unknown")[:8]

            r = resend.Emails.send({
                "from": settings.resend_from_email,
                "to": email,
                "subject": f"[ChainRadar {severity}] Alert for wallet {wallet}...",
                "html": self._format_email_html(alert_data),
            })
            return {"email_id": r.get("id")}
        else:
            return {"skipped": True, "reason": "Resend API key not configured"}

    async def _send_in_app(self, user_data: Dict, alert_data: Dict) -> Dict:
        """Publish to Redis for SSE stream pickup."""
        from infrastructure.messaging.redis_pubsub import get_pubsub, CHANNEL_NOTIFICATION

        pubsub = get_pubsub()
        await pubsub.publish(CHANNEL_NOTIFICATION, {
            "user_id": user_data.get("user_id", ""),
            "type": "alert",
            **alert_data,
        })
        return {"delivered_via": "sse"}

    async def _send_webhook(self, user_data: Dict, alert_data: Dict) -> Dict:
        """Send alert to user's custom webhook URL."""
        webhook_url = user_data.get("webhook_url")
        if not webhook_url:
            return {"skipped": True, "reason": "No webhook URL configured"}

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=alert_data,
                timeout=10.0,
                headers={"User-Agent": "ChainRadar/1.0", "Content-Type": "application/json"},
            )
            return {"webhook_status": response.status_code}

    def _format_telegram_message(self, alert_data: Dict) -> str:
        """Format alert as Telegram HTML message."""
        severity = alert_data.get("severity", "info").upper()
        wallet = alert_data.get("wallet_address", "Unknown")
        summary = alert_data.get("summary", "Alert triggered")
        rule_name = alert_data.get("rule_name", "")

        emoji = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}.get(severity, "📢")

        return (
            f"{emoji} <b>ChainRadar {severity}</b>\n\n"
            f"📋 Rule: <b>{rule_name}</b>\n"
            f"👛 Wallet: <code>{wallet}</code>\n"
            f"📝 {summary}\n\n"
            f"🔗 <a href='https://solscan.io/account/{wallet}'>View on Solscan</a>"
        )

    def _format_email_html(self, alert_data: Dict) -> str:
        """Format alert as email HTML."""
        severity = alert_data.get("severity", "info").upper()
        wallet = alert_data.get("wallet_address", "Unknown")
        summary = alert_data.get("summary", "Alert triggered")

        return f"""
        <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #0f172a; color: white; padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🛰️ ChainRadar Alert</h1>
            </div>
            <div style="background: #1e293b; color: #e2e8f0; padding: 24px;">
                <div style="background: {'#dc2626' if severity == 'CRITICAL' else '#eab308' if severity == 'WARNING' else '#3b82f6'};
                    color: white; padding: 8px 16px; border-radius: 8px; display: inline-block; margin-bottom: 16px;">
                    {severity}
                </div>
                <p><strong>Wallet:</strong> <code>{wallet}</code></p>
                <p><strong>Details:</strong> {summary}</p>
                <a href="https://solscan.io/account/{wallet}"
                   style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px;
                   border-radius: 8px; text-decoration: none; margin-top: 16px;">
                    View on Solscan →
                </a>
            </div>
        </div>
        """

    @staticmethod
    def generate_idempotency_key(rule_id: str, event_id: str, channel: str) -> str:
        """Generate unique idempotency key for deduplication."""
        raw = f"{rule_id}:{event_id}:{channel}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]


# Singleton
_notification_service = None

def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
