"""
WaspNet — Wallets Router
CRUD operations for wallet watchlist management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from infrastructure.db.models import UserModel
from infrastructure.db.repositories.pg_wallet_repo import PgWalletRepository
from interface.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/wallets", tags=["Wallets"])


class AddWalletRequest(BaseModel):
    address: str = Field(..., min_length=32, max_length=100)
    network: str = Field(default="solana", pattern=r"^(solana|ethereum|polygon|arbitrum|base)$")
    label: Optional[str] = Field(None, max_length=200)


class WalletResponse(BaseModel):
    id: str
    address: str
    network: str
    label: Optional[str]
    is_active: bool
    last_balance_lamports: Optional[float]
    created_at: str

    class Config:
        from_attributes = True


class UpdateWalletRequest(BaseModel):
    label: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


def _to_response(w) -> WalletResponse:
    return WalletResponse(
        id=str(w.id), address=w.address, network=w.network,
        label=w.label, is_active=w.is_active,
        last_balance_lamports=w.last_balance_lamports,
        created_at=w.created_at.isoformat(),
    )


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def add_wallet(
    body: AddWalletRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PgWalletRepository(db)
    existing = await repo.get_by_address(body.address, user.id)
    if existing:
        raise HTTPException(status_code=409, detail="Wallet already in watchlist")
    wallet = await repo.create(user_id=user.id, address=body.address, network=body.network, label=body.label)
    return _to_response(wallet)


@router.get("", response_model=List[WalletResponse])
async def list_wallets(
    active_only: bool = True,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PgWalletRepository(db)
    wallets = await repo.list_by_user(user.id, active_only=active_only)
    return [_to_response(w) for w in wallets]


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(wallet_id: UUID, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PgWalletRepository(db)
    wallet = await repo.get_by_id(wallet_id)
    if not wallet or wallet.user_id != user.id:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return _to_response(wallet)


@router.patch("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(wallet_id: UUID, body: UpdateWalletRequest, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PgWalletRepository(db)
    wallet = await repo.get_by_id(wallet_id)
    if not wallet or wallet.user_id != user.id:
        raise HTTPException(status_code=404, detail="Wallet not found")
    update_data = body.model_dump(exclude_unset=True)
    if update_data:
        await repo.update(wallet_id, **update_data)
        await db.flush()
        wallet = await repo.get_by_id(wallet_id)
    return _to_response(wallet)


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(wallet_id: UUID, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PgWalletRepository(db)
    wallet = await repo.get_by_id(wallet_id)
    if not wallet or wallet.user_id != user.id:
        raise HTTPException(status_code=404, detail="Wallet not found")
    await repo.delete(wallet_id)
