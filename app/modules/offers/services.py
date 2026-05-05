"""Offers module — service layer."""

from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models import Course
from app.modules.offers.models import Offer, OfferRedemption
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_offer(db: AsyncSession, data: dict) -> Offer:
    """Admin creates a new offer."""
    # Check code uniqueness
    existing = await db.execute(select(Offer).where(Offer.code == data["code"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Offer code already exists")

    offer = Offer(
        title=data["title"],
        description=data.get("description"),
        discount_type=data.get("discount_type", "percentage"),
        discount_value=data["discount_value"],
        code=data["code"],
        course_id=data.get("course_id"),
        created_by_admin=data.get("created_by_admin"),
        distributor_id=data.get("distributor_id"),
        max_redemptions=data.get("max_redemptions", 0),
        is_active=data.get("is_active", True),
        valid_from=data.get("valid_from", datetime.now(timezone.utc)),
        valid_until=data.get("valid_until"),
    )
    db.add(offer)
    await db.flush()
    await db.refresh(offer)
    logger.info("offer_created", offer_id=offer.id, code=offer.code)
    return offer


async def list_offers(db: AsyncSession, active_only: bool = True) -> List[Offer]:
    """List available offers."""
    query = select(Offer).order_by(Offer.created_at.desc())
    if active_only:
        now = datetime.now(timezone.utc)
        query = query.where(
            Offer.is_active == True,  # noqa: E712
            Offer.valid_from <= now,
        )
    result = await db.execute(query)
    return list(result.scalars().all())


async def apply_offer(db: AsyncSession, user_id: int, code: str, course_id: int) -> dict:
    """Apply an offer code to a course purchase."""
    # Find the offer
    result = await db.execute(select(Offer).where(Offer.code == code))
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Invalid offer code")

    if not offer.is_active:
        raise HTTPException(status_code=400, detail="Offer is no longer active")

    now = datetime.now(timezone.utc)
    if offer.valid_until and now > offer.valid_until:
        raise HTTPException(status_code=400, detail="Offer has expired")

    if offer.max_redemptions > 0 and offer.current_redemptions >= offer.max_redemptions:
        raise HTTPException(status_code=400, detail="Offer redemption limit reached")

    # Course-specific offer check
    if offer.course_id and offer.course_id != course_id:
        raise HTTPException(status_code=400, detail="Offer is not valid for this course")

    # Check if user already redeemed this offer
    redeemed = await db.execute(
        select(OfferRedemption).where(
            OfferRedemption.offer_id == offer.id,
            OfferRedemption.user_id == user_id,
        )
    )
    if redeemed.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You have already redeemed this offer")

    # Get course price
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    original_price = course.price or 0.0
    if offer.discount_type == "percentage":
        discount = original_price * (offer.discount_value / 100)
    else:
        discount = offer.discount_value
    discounted_price = max(original_price - discount, 0.0)

    # Record redemption
    redemption = OfferRedemption(
        offer_id=offer.id,
        user_id=user_id,
        original_price=original_price,
        discounted_price=discounted_price,
    )
    db.add(redemption)
    offer.current_redemptions += 1
    await db.flush()

    logger.info("offer_applied", user_id=user_id, offer_id=offer.id, discount=discount)
    return {
        "offer_id": offer.id,
        "original_price": original_price,
        "discounted_price": round(discounted_price, 2),
        "discount_applied": round(discount, 2),
        "message": f"Offer '{offer.code}' applied successfully",
    }


async def update_offer(db: AsyncSession, offer_id: int, data: dict) -> Offer:
    """Update an existing offer/coupon."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    for key, value in data.items():
        if value is not None and hasattr(offer, key):
            setattr(offer, key, value)

    await db.commit()
    await db.refresh(offer)
    logger.info("offer_updated", offer_id=offer.id)
    return offer


async def delete_offer(db: AsyncSession, offer_id: int) -> None:
    """Delete an offer/coupon."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    await db.delete(offer)
    await db.commit()
    logger.info("offer_deleted", offer_id=offer_id)


async def toggle_offer(db: AsyncSession, offer_id: int) -> Offer:
    """Toggle an offer's active status."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    offer.is_active = not offer.is_active
    await db.commit()
    await db.refresh(offer)
    logger.info("offer_toggled", offer_id=offer.id, is_active=offer.is_active)
    return offer


async def get_offer_stats(db: AsyncSession) -> dict:
    """Get coupon/offer usage statistics."""
    result = await db.execute(select(Offer))
    offers = list(result.scalars().all())

    active = [o for o in offers if o.is_active]
    total_usage = sum(o.current_redemptions for o in offers)

    return {
        "total_coupons": len(offers),
        "active_coupons": len(active),
        "total_usage": total_usage,
        "expired_coupons": sum(
            1 for o in offers
            if o.valid_until and o.valid_until < datetime.now(timezone.utc)
        ),
    }
