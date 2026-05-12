"""
ChainRadar — Alerts Router
CRUD for alert rules + alert history.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from infrastructure.db.models import UserModel
from infrastructure.db.repositories.pg_alert_repo import PgAlertRuleRepository
from infrastructure.db.repositories.pg_wallet_repo import PgWalletRepository
from interface.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alert Rules"])


class ConditionSchema(BaseModel):
    condition_type: str = Field(..., pattern=r"^(balance_above|balance_below|balance_change|large_transfer|whale_movement|token_transfer|new_token|program_interaction)$")
    threshold: float = Field(..., gt=0)
    comparison: str = Field(default="gte", pattern=r"^(gte|lte|eq|gt|lt)$")
    token_mint: Optional[str] = None
    program_id: Optional[str] = None


class CreateAlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    wallet_id: str
    conditions: List[ConditionSchema] = Field(..., min_length=1)
    severity: str = Field(default="warning", pattern=r"^(critical|warning|info)$")
    delivery_channels: List[str] = Field(default=["in_app"])
    cooldown_minutes: int = Field(default=5, ge=1, le=1440)


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    wallet_id: str
    conditions: list
    severity: str
    delivery_channels: list
    is_active: bool
    cooldown_minutes: int
    trigger_count: int
    last_triggered_at: Optional[str]
    created_at: str


def _to_response(r) -> AlertRuleResponse:
    return AlertRuleResponse(
        id=str(r.id), name=r.name, wallet_id=str(r.wallet_id),
        conditions=r.conditions, severity=r.severity,
        delivery_channels=r.delivery_channels, is_active=r.is_active,
        cooldown_minutes=r.cooldown_minutes, trigger_count=r.trigger_count,
        last_triggered_at=r.last_triggered_at.isoformat() if r.last_triggered_at else None,
        created_at=r.created_at.isoformat(),
    )


@router.post("", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    body: CreateAlertRuleRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet_repo = PgWalletRepository(db)
    wallet = await wallet_repo.get_by_id(UUID(body.wallet_id))
    if not wallet or wallet.user_id != user.id:
        raise HTTPException(status_code=404, detail="Wallet not found")

    repo = PgAlertRuleRepository(db)
    rule = await repo.create({
        "user_id": user.id,
        "wallet_id": wallet.id,
        "name": body.name,
        "conditions": [c.model_dump() for c in body.conditions],
        "severity": body.severity,
        "delivery_channels": body.delivery_channels,
        "cooldown_minutes": body.cooldown_minutes,
    })
    return _to_response(rule)


@router.get("", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    active_only: bool = True,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PgAlertRuleRepository(db)
    rules = await repo.list_by_user(user.id, active_only=active_only)
    return [_to_response(r) for r in rules]


@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(rule_id: UUID, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PgAlertRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if not rule or rule.user_id != user.id:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return _to_response(rule)


@router.patch("/{rule_id}", response_model=AlertRuleResponse)
async def toggle_alert_rule(rule_id: UUID, is_active: bool, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PgAlertRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if not rule or rule.user_id != user.id:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await repo.update(rule_id, is_active=is_active)
    await db.flush()
    rule = await repo.get_by_id(rule_id)
    return _to_response(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(rule_id: UUID, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PgAlertRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if not rule or rule.user_id != user.id:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await repo.delete(rule_id)
