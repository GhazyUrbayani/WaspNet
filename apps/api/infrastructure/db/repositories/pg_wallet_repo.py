"""
ChainRadar — PostgreSQL Wallet Repository Implementation
Implements WalletRepository interface using SQLAlchemy async.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.wallet_repo import WalletRepository
from infrastructure.db.models import WatchedWalletModel


class PgWalletRepository(WalletRepository):
    """PostgreSQL implementation of WalletRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user_id: UUID, address: str, network: str, label: Optional[str] = None):
        wallet = WatchedWalletModel(
            user_id=user_id,
            address=address,
            network=network,
            label=label,
        )
        self._session.add(wallet)
        await self._session.flush()
        return wallet

    async def get_by_id(self, wallet_id: UUID):
        result = await self._session.execute(
            select(WatchedWalletModel).where(WatchedWalletModel.id == wallet_id)
        )
        return result.scalar_one_or_none()

    async def get_by_address(self, address: str, user_id: UUID):
        result = await self._session.execute(
            select(WatchedWalletModel).where(
                WatchedWalletModel.address == address,
                WatchedWalletModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, active_only: bool = True):
        query = select(WatchedWalletModel).where(WatchedWalletModel.user_id == user_id)
        if active_only:
            query = query.where(WatchedWalletModel.is_active == True)
        query = query.order_by(WatchedWalletModel.created_at.desc())
        result = await self._session.execute(query)
        return result.scalars().all()

    async def update(self, wallet_id: UUID, **kwargs):
        kwargs["updated_at"] = datetime.utcnow()
        await self._session.execute(
            update(WatchedWalletModel)
            .where(WatchedWalletModel.id == wallet_id)
            .values(**kwargs)
        )

    async def delete(self, wallet_id: UUID):
        wallet = await self.get_by_id(wallet_id)
        if wallet:
            await self._session.delete(wallet)

    async def get_all_active_addresses(self) -> List[str]:
        result = await self._session.execute(
            select(WatchedWalletModel.address)
            .where(WatchedWalletModel.is_active == True)
            .distinct()
        )
        return [row[0] for row in result.all()]
