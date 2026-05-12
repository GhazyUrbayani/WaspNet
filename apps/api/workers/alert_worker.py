"""
ChainRadar — Celery Alert Worker
Background task processor for alert evaluation and delivery.
ARCH: Consumes Redis events, evaluates rules, delivers notifications.
"""

from celery import Celery
from config import get_settings

settings = get_settings()

# Initialize Celery with Redis as broker and backend
celery_app = Celery(
    "chainradar",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # ARCH: Ack after completion for reliability
    worker_prefetch_multiplier=1,  # Process one task at a time
)


@celery_app.task(
    name="chainradar.evaluate_and_notify",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
)
def evaluate_and_notify(self, event_data: dict):
    """
    Main alert processing task.
    Flow: webhook event → evaluate rules → deliver notifications.

    ARCH: This runs in a separate Celery worker process.
    Uses synchronous DB calls since Celery doesn't support async natively.
    """
    import asyncio

    try:
        asyncio.run(_process_alert(event_data))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _process_alert(event_data: dict):
    """Async alert processing logic."""
    from application.use_cases.evaluate_rules import evaluate_rules
    from application.services.notification_service import get_notification_service

    wallet_address = event_data.get("wallet_address", "")
    if not wallet_address:
        return

    # Get active rules for this wallet from DB
    from database import async_session_factory
    from infrastructure.db.repositories.pg_alert_repo import PgAlertRuleRepository

    async with async_session_factory() as session:
        repo = PgAlertRuleRepository(session)
        rules_models = await repo.list_by_wallet(wallet_address, active_only=True)

        # Convert to dicts for pure-function evaluator
        rules = []
        for r in rules_models:
            rules.append({
                "id": str(r.id),
                "conditions": r.conditions,
                "severity": r.severity,
                "delivery_channels": r.delivery_channels,
                "cooldown_minutes": r.cooldown_minutes,
                "last_triggered_at": r.last_triggered_at,
                "user_id": str(r.user_id),
                "name": r.name,
            })

    if not rules:
        return

    # Evaluate rules
    wallet_data = event_data.get("data", {})
    results = evaluate_rules(rules, wallet_data, event_data)

    # Deliver notifications for triggered rules
    notification_service = get_notification_service()

    for result in results:
        if not result.triggered:
            continue

        # Find the rule data
        rule = next((r for r in rules if r["id"] == result.rule_id), None)
        if not rule:
            continue

        # Get user data for delivery
        from infrastructure.db.models import UserModel
        from sqlalchemy import select

        async with async_session_factory() as session:
            user_result = await session.execute(
                select(UserModel).where(UserModel.id == rule["user_id"])
            )
            user = user_result.scalar_one_or_none()
            if not user:
                continue

            user_data = {
                "user_id": str(user.id),
                "email": user.email,
                "telegram_chat_id": user.telegram_chat_id,
            }

            # Mark rule as triggered
            repo = PgAlertRuleRepository(session)
            await repo.mark_triggered(result.rule_id)
            await session.commit()

        # Deliver to each channel
        alert_data = {
            "rule_name": rule["name"],
            "wallet_address": wallet_address,
            "severity": result.severity,
            "summary": result.summary,
            "matched_conditions": result.matched_conditions,
        }

        for channel in rule.get("delivery_channels", ["in_app"]):
            idempotency_key = notification_service.generate_idempotency_key(
                result.rule_id,
                event_data.get("id", ""),
                channel,
            )
            await notification_service.deliver(
                channel=channel,
                user_data=user_data,
                alert_data=alert_data,
                idempotency_key=idempotency_key,
            )
