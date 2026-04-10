"""Simulator module — trading engine, risk management, and analytics."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.simulator.models import (
    SimulatorAccount, SimulatorProfile, Trade, Position, Order,
    PerformanceMetric,
)
from app.modules.certificates.models import Certificate


# ═════════════════════════════════════════════════════════════════════
# ACCOUNT MANAGEMENT
# ═════════════════════════════════════════════════════════════════════

async def create_account(
    db: AsyncSession, user_id: int, profile_id: Optional[int] = None
) -> SimulatorAccount:
    """Create a simulator account. Requires at least one certificate."""

    # Security: only certified students
    cert_result = await db.execute(
        select(Certificate).where(Certificate.user_id == user_id).limit(1)
    )
    if cert_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=403,
            detail="You must complete at least one course and earn a certificate before accessing the simulator.",
        )

    # Check existing account
    existing = await db.execute(
        select(SimulatorAccount).where(
            SimulatorAccount.user_id == user_id,
            SimulatorAccount.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Active simulator account already exists")

    initial_balance = 100000.0
    if profile_id:
        profile = await db.get(SimulatorProfile, profile_id)
        if profile and profile.is_active:
            initial_balance = profile.initial_balance
        else:
            raise HTTPException(status_code=404, detail="Simulator profile not found")

    account = SimulatorAccount(
        user_id=user_id,
        profile_id=profile_id,
        balance=initial_balance,
        initial_balance=initial_balance,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


async def get_user_account(db: AsyncSession, user_id: int) -> SimulatorAccount:
    """Get the user's active simulator account."""
    result = await db.execute(
        select(SimulatorAccount).where(
            SimulatorAccount.user_id == user_id,
            SimulatorAccount.is_active == True,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="No active simulator account. Start one first.")
    return account


# ═════════════════════════════════════════════════════════════════════
# RISK MANAGEMENT ENGINE
# ═════════════════════════════════════════════════════════════════════

async def _check_risk_rules(
    db: AsyncSession, account: SimulatorAccount, quantity: float, price: float,
    stop_loss: Optional[float], side: str,
):
    """Validate trade against risk rules. Raises HTTPException on violation."""

    position_value = quantity * price

    # Load profile rules if available
    daily_loss_limit = 5000.0
    max_position_size = 50000.0
    stop_loss_required = True

    if account.profile_id:
        profile = await db.get(SimulatorProfile, account.profile_id)
        if profile:
            daily_loss_limit = profile.daily_loss_limit
            max_position_size = profile.max_position_size
            stop_loss_required = profile.stop_loss_required

    # Rule 1: Max position size
    if position_value > max_position_size:
        raise HTTPException(
            status_code=400,
            detail=f"Position size ${position_value:.2f} exceeds max ${max_position_size:.2f}",
        )

    # Rule 2: Stop-loss required
    if stop_loss_required and stop_loss is None:
        raise HTTPException(
            status_code=400,
            detail="Stop-loss is required for this profile",
        )

    # Rule 3: Daily loss limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_loss_result = await db.execute(
        select(func.coalesce(func.sum(Trade.pnl), 0.0)).where(
            Trade.account_id == account.id,
            Trade.status == "closed",
            Trade.closed_at >= today_start,
            Trade.pnl < 0,
        )
    )
    daily_loss = abs(daily_loss_result.scalar() or 0.0)
    if daily_loss >= daily_loss_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Daily loss limit reached (${daily_loss:.2f} / ${daily_loss_limit:.2f})",
        )

    # Rule 4: Sufficient balance
    if position_value > account.balance:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Required: ${position_value:.2f}, Available: ${account.balance:.2f}",
        )


# ═════════════════════════════════════════════════════════════════════
# TRADING ENGINE
# ═════════════════════════════════════════════════════════════════════

async def open_trade(
    db: AsyncSession, user_id: int,
    symbol: str, side: str, quantity: float, price: float,
    stop_loss: Optional[float] = None, take_profit: Optional[float] = None,
) -> Trade:
    """Open a new trade with risk validation."""
    account = await get_user_account(db, user_id)

    # Validate risk rules
    await _check_risk_rules(db, account, quantity, price, stop_loss, side)

    # Deduct margin from balance
    margin = quantity * price
    account.balance -= margin

    # Create trade record
    trade = Trade(
        account_id=account.id,
        symbol=symbol.upper(),
        side=side,
        quantity=quantity,
        entry_price=price,
        status="open",
    )
    db.add(trade)

    # Create position
    position = Position(
        account_id=account.id,
        symbol=symbol.upper(),
        side=side,
        quantity=quantity,
        entry_price=price,
        current_price=price,
        unrealized_pnl=0.0,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )
    db.add(position)

    # Create order record
    order = Order(
        account_id=account.id,
        symbol=symbol.upper(),
        side=side,
        order_type="market",
        quantity=quantity,
        price=price,
        status="filled",
    )
    db.add(order)

    await db.flush()
    await db.refresh(trade)
    return trade


async def close_position(
    db: AsyncSession, user_id: int, position_id: int, exit_price: float,
) -> Trade:
    """Close an open position and calculate PnL."""
    account = await get_user_account(db, user_id)

    result = await db.execute(
        select(Position).where(
            Position.id == position_id,
            Position.account_id == account.id,
        )
    )
    position = result.scalar_one_or_none()
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")

    # Calculate PnL
    if position.side == "buy":
        pnl = (exit_price - position.entry_price) * position.quantity
    else:
        pnl = (position.entry_price - exit_price) * position.quantity

    # Update account balance (return margin + pnl)
    margin = position.quantity * position.entry_price
    account.balance += margin + pnl

    # Update the corresponding trade
    trade_result = await db.execute(
        select(Trade).where(
            Trade.account_id == account.id,
            Trade.symbol == position.symbol,
            Trade.status == "open",
        ).order_by(Trade.opened_at.desc()).limit(1)
    )
    trade = trade_result.scalar_one_or_none()
    if trade:
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.status = "closed"
        trade.closed_at = datetime.now(timezone.utc)

    # Remove position
    await db.delete(position)
    await db.flush()

    if trade:
        await db.refresh(trade)
        return trade

    # Fallback: return a dummy trade response if no matching trade found
    raise HTTPException(status_code=404, detail="Matching trade not found")


async def get_positions(db: AsyncSession, user_id: int) -> List[Position]:
    """List all open positions for the user."""
    account = await get_user_account(db, user_id)
    result = await db.execute(
        select(Position).where(Position.account_id == account.id)
    )
    return list(result.scalars().all())


async def get_trades(db: AsyncSession, user_id: int) -> List[Trade]:
    """List trade history for the user."""
    account = await get_user_account(db, user_id)
    result = await db.execute(
        select(Trade).where(Trade.account_id == account.id).order_by(Trade.opened_at.desc())
    )
    return list(result.scalars().all())


# ═════════════════════════════════════════════════════════════════════
# PROP FIRM PROFILES
# ═════════════════════════════════════════════════════════════════════

async def get_profiles(db: AsyncSession) -> List[SimulatorProfile]:
    """List all active simulator profiles."""
    result = await db.execute(
        select(SimulatorProfile).where(SimulatorProfile.is_active == True)
    )
    return list(result.scalars().all())


# ═════════════════════════════════════════════════════════════════════
# PERFORMANCE ANALYTICS
# ═════════════════════════════════════════════════════════════════════

async def compute_performance(db: AsyncSession, user_id: int) -> PerformanceMetric:
    """Compute and store performance metrics from trade history."""
    account = await get_user_account(db, user_id)

    # Fetch all closed trades
    result = await db.execute(
        select(Trade).where(
            Trade.account_id == account.id,
            Trade.status == "closed",
        )
    )
    closed_trades = list(result.scalars().all())

    total_trades = len(closed_trades)
    if total_trades == 0:
        raise HTTPException(status_code=400, detail="No closed trades to analyse")

    winning = [t for t in closed_trades if (t.pnl or 0) > 0]
    losing = [t for t in closed_trades if (t.pnl or 0) < 0]

    winning_trades = len(winning)
    losing_trades = len(losing)
    total_pnl = sum(t.pnl or 0 for t in closed_trades)
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
    avg_win = (sum(t.pnl for t in winning) / winning_trades) if winning_trades > 0 else 0.0
    avg_loss = (sum(t.pnl for t in losing) / losing_trades) if losing_trades > 0 else 0.0

    # Max drawdown calculation
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for t in sorted(closed_trades, key=lambda x: x.closed_at or x.opened_at):
        cumulative += (t.pnl or 0)
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Risk score (0-100, lower is better): based on loss ratio and drawdown
    loss_ratio = losing_trades / total_trades if total_trades > 0 else 0.5
    drawdown_ratio = max_drawdown / account.initial_balance if account.initial_balance > 0 else 0
    risk_score = min(100.0, (loss_ratio * 50) + (drawdown_ratio * 50))

    # Consistency score (0-100): based on trade frequency and win rate stability
    consistency_score = min(100.0, win_rate * 0.7 + min(total_trades, 50) * 0.6)

    # Upsert performance metric
    existing = await db.execute(
        select(PerformanceMetric).where(PerformanceMetric.account_id == account.id)
    )
    metric = existing.scalar_one_or_none()
    if metric is None:
        metric = PerformanceMetric(account_id=account.id)
        db.add(metric)

    metric.total_trades = total_trades
    metric.winning_trades = winning_trades
    metric.losing_trades = losing_trades
    metric.total_pnl = round(total_pnl, 2)
    metric.win_rate = round(win_rate, 2)
    metric.avg_win = round(avg_win, 2)
    metric.avg_loss = round(avg_loss, 2)
    metric.max_drawdown = round(max_drawdown, 2)
    metric.risk_score = round(risk_score, 2)
    metric.consistency_score = round(consistency_score, 2)
    metric.computed_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(metric)
    return metric
