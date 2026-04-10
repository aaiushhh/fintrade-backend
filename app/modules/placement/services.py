"""Placement module — evaluation service based on simulator metrics."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.placement.models import PlacementResult
from app.modules.simulator.models import SimulatorAccount, PerformanceMetric


# ── Eligibility thresholds ───────────────────────────────────────────
MIN_WIN_RATE = 50.0
MAX_RISK_SCORE = 40.0
MIN_TOTAL_TRADES = 20


async def get_placement_status(db: AsyncSession, user_id: int) -> dict:
    """Check if a placement evaluation exists for the user."""
    result = await db.execute(
        select(PlacementResult).where(PlacementResult.user_id == user_id)
    )
    placement = result.scalar_one_or_none()
    if placement is None:
        return {"evaluated": False}

    return {
        "evaluated": True,
        "eligible": placement.eligible,
        "score": placement.score,
        "criteria": placement.criteria_snapshot,
        "evaluated_at": placement.evaluated_at,
    }


async def evaluate_placement(db: AsyncSession, user_id: int) -> dict:
    """Evaluate placement eligibility based on simulator performance."""

    # 1. Find user's simulator account
    account_result = await db.execute(
        select(SimulatorAccount).where(
            SimulatorAccount.user_id == user_id,
            SimulatorAccount.is_active == True,
        )
    )
    account = account_result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=400, detail="No simulator account found. Start trading first.")

    # 2. Find performance metrics
    metric_result = await db.execute(
        select(PerformanceMetric).where(PerformanceMetric.account_id == account.id)
    )
    metric = metric_result.scalar_one_or_none()
    if metric is None:
        raise HTTPException(
            status_code=400,
            detail="No performance data found. Complete trades and compute performance first.",
        )

    # 3. Evaluate eligibility
    criteria = {
        "win_rate": metric.win_rate,
        "risk_score": metric.risk_score,
        "total_trades": metric.total_trades,
        "total_pnl": metric.total_pnl,
        "consistency_score": metric.consistency_score,
        "thresholds": {
            "min_win_rate": MIN_WIN_RATE,
            "max_risk_score": MAX_RISK_SCORE,
            "min_total_trades": MIN_TOTAL_TRADES,
        },
    }

    eligible = (
        metric.win_rate >= MIN_WIN_RATE
        and metric.risk_score <= MAX_RISK_SCORE
        and metric.total_trades >= MIN_TOTAL_TRADES
    )

    # Weighted composite score
    score = round(
        (metric.win_rate * 0.4)
        + (metric.consistency_score * 0.3)
        + (max(0, metric.total_pnl) / account.initial_balance * 100 * 0.3),
        2,
    )

    # 4. Upsert result
    existing = await db.execute(
        select(PlacementResult).where(PlacementResult.user_id == user_id)
    )
    placement = existing.scalar_one_or_none()
    if placement is None:
        placement = PlacementResult(user_id=user_id)
        db.add(placement)

    placement.eligible = eligible
    placement.score = score
    placement.criteria_snapshot = criteria
    placement.evaluated_at = datetime.now(timezone.utc)

    await db.flush()

    message = "Congratulations! You are eligible for placement." if eligible else "Not yet eligible. Keep practicing."
    return {
        "eligible": eligible,
        "score": score,
        "criteria": criteria,
        "message": message,
    }
