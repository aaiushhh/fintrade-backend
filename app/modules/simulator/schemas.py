"""Simulator module — Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Requests ─────────────────────────────────────────────────────────

class SimulatorStartRequest(BaseModel):
    profile_id: Optional[int] = None  # use default profile if None


class TradeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    side: str = Field(..., pattern="^(buy|sell)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)  # Mock price; future: from TradingView API
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class ClosePositionRequest(BaseModel):
    position_id: int
    exit_price: float = Field(..., gt=0)  # Mock price; future: from TradingView API


# ── Responses ────────────────────────────────────────────────────────

class SimulatorAccountResponse(BaseModel):
    id: int
    user_id: int
    profile_id: Optional[int] = None
    balance: float
    initial_balance: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeResponse(BaseModel):
    id: int
    account_id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PositionResponse(BaseModel):
    id: int
    account_id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime

    model_config = {"from_attributes": True}


class SimulatorProfileResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    initial_balance: float
    daily_loss_limit: float
    max_position_size: float
    stop_loss_required: bool
    is_active: bool

    model_config = {"from_attributes": True}


class PerformanceResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    risk_score: float
    consistency_score: float
    computed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
