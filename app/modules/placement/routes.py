"""Placement module — API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.modules.auth.models import User
from app.modules.placement import schemas, services

router = APIRouter(prefix="/placement", tags=["Placement"])


@router.get("/status", response_model=schemas.PlacementStatusResponse)
async def placement_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check current placement eligibility status."""
    data = await services.get_placement_status(db, current_user.id)
    return schemas.PlacementStatusResponse(**data)


@router.post("/evaluate", response_model=schemas.PlacementEvaluateResponse)
async def evaluate_placement(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger placement evaluation based on simulator metrics."""
    data = await services.evaluate_placement(db, current_user.id)
    return schemas.PlacementEvaluateResponse(**data)
