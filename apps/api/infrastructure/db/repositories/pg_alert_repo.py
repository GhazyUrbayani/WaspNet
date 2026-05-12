"""
ChainRadar — PostgreSQL Alert Rule Repository Implementation
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.wallet_repo import AlertRuleRepository
from infrastructure.db.models import AlertRuleModel, WatchedWalletModel


class PgAlertRuleRepository(AlertRuleRepository):
    """PostgreSQL implementation of AlertRuleRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, rule_data: dict):
        rule = AlertRuleModel(**rule_data)
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_by_id(self, rule_id: UUID):
        result = await self._session.execute(
            select(AlertRuleModel).where(AlertRuleModel.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, active_only: bool = True):
        query = select(AlertRuleModel).where(AlertRuleModel.user_id == user_id)
        if active_only:
            query = query.where(AlertRuleModel.is_active == True)
        query = query.order_by(AlertRuleModel.created_at.desc())
        result = await self._session.execute(query)
        return result.scalars().all()

    async def list_by_wallet(self, wallet_address: str, active_only: bool = True):
        """
        Get all active alert rules for a wallet address across all users.
        Used by webhook handler to evaluate rules when an event arrives.
        """
        query = (
            select(AlertRuleModel)
            .join(WatchedWalletModel, AlertRuleModel.wallet_id == WatchedWalletModel.id)
            .where(WatchedWalletModel.address == wallet_address)
        )
        if active_only:
            query = query.where(AlertRuleModel.is_active == True)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def update(self, rule_id: UUID, **kwargs):
        kwargs["updated_at"] = datetime.utcnow()
        await self._session.execute(
            update(AlertRuleModel)
            .where(AlertRuleModel.id == rule_id)
            .values(**kwargs)
        )

    async def delete(self, rule_id: UUID):
        rule = await self.get_by_id(rule_id)
        if rule:
            await self._session.delete(rule)

    async def mark_triggered(self, rule_id: UUID):
        await self._session.execute(
            update(AlertRuleModel)
            .where(AlertRuleModel.id == rule_id)
            .values(
                last_triggered_at=datetime.utcnow(),
                trigger_count=AlertRuleModel.trigger_count + 1,
            )
        )
