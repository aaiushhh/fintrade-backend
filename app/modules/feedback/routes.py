"""Feedback module — API routes."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.db.database import get_db
from app.modules.auth.models import User
from app.modules.feedback import schemas, services

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=schemas.FeedbackResponse, status_code=201)
async def submit_feedback(
    req: schemas.FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback (any authenticated user)."""
    fb = await services.submit_feedback(
        db, current_user.id,
        rating=req.rating, comments=req.comments, course_id=req.course_id,
    )
    return schemas.FeedbackResponse.model_validate(fb)


@router.get("", response_model=List[schemas.FeedbackResponse])
async def list_feedback(
    _admin: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """List all feedback (admin only)."""
    items = await services.list_all_feedback(db)
    return [schemas.FeedbackResponse.model_validate(f) for f in items]


@router.get("/my", response_model=List[schemas.FeedbackResponse])
async def my_feedback(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List my feedback submissions."""
    items = await services.list_user_feedback(db, current_user.id)
    return [schemas.FeedbackResponse.model_validate(f) for f in items]
