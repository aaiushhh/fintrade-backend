"""Feedback module — service layer."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feedback.models import Feedback


async def submit_feedback(
    db: AsyncSession, user_id: int, rating: int,
    comments: Optional[str] = None, course_id: Optional[int] = None,
) -> Feedback:
    """Submit student feedback."""
    fb = Feedback(
        user_id=user_id,
        course_id=course_id,
        rating=rating,
        comments=comments,
    )
    db.add(fb)
    await db.flush()
    await db.refresh(fb)
    return fb


async def list_all_feedback(db: AsyncSession) -> List[Feedback]:
    """List all feedback (admin view)."""
    result = await db.execute(
        select(Feedback).order_by(Feedback.created_at.desc())
    )
    return list(result.scalars().all())


async def list_user_feedback(db: AsyncSession, user_id: int) -> List[Feedback]:
    """List feedback submitted by a specific user."""
    result = await db.execute(
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(Feedback.created_at.desc())
    )
    return list(result.scalars().all())
