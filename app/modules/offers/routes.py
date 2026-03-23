"""Offers module — API routes."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.db.database import get_db
from app.modules.auth.models import User
from app.modules.offers import schemas, services

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.get("", response_model=List[schemas.OfferResponse])
async def list_offers(db: AsyncSession = Depends(get_db)):
    """List all active offers."""
    offers = await services.list_offers(db)
    return [schemas.OfferResponse.model_validate(o) for o in offers]


@router.post("/apply", response_model=schemas.OfferApplyResponse)
async def apply_offer(
    body: schemas.OfferApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply an offer code to a course."""
    result = await services.apply_offer(db, current_user.id, body.code, body.course_id)
    return schemas.OfferApplyResponse(**result)
