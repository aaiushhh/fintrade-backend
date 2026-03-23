"""Distributors module — API routes (distributor role)."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.db.database import get_db
from app.modules.auth.models import User
from app.modules.distributors import schemas, services

router = APIRouter(prefix="/distributor", tags=["Distributor"])


@router.get("/profile", response_model=schemas.DistributorProfileResponse)
async def get_profile(
    current_user: User = Depends(require_roles(["distributor"])),
    db: AsyncSession = Depends(get_db),
):
    """Get the current distributor's profile."""
    dist = await services.get_distributor_by_user_id(db, current_user.id)
    return schemas.DistributorProfileResponse(
        id=dist.id,
        user_id=dist.user_id,
        region=dist.region,
        referral_code=dist.referral_code,
        discount_percentage=dist.discount_percentage,
        created_at=dist.created_at,
        user_name=dist.user.full_name if dist.user else None,
        user_email=dist.user.email if dist.user else None,
    )


@router.get("/referral-code", response_model=schemas.ReferralCodeResponse)
async def get_referral_code(
    current_user: User = Depends(require_roles(["distributor"])),
    db: AsyncSession = Depends(get_db),
):
    """Get the distributor's referral code and discount info."""
    dist = await services.get_distributor_by_user_id(db, current_user.id)
    return schemas.ReferralCodeResponse(
        referral_code=dist.referral_code,
        discount_percentage=dist.discount_percentage,
        region=dist.region,
    )


@router.get("/referrals", response_model=List[schemas.ReferralResponse])
async def get_referrals(
    current_user: User = Depends(require_roles(["distributor"])),
    db: AsyncSession = Depends(get_db),
):
    """List all students referred by this distributor."""
    dist = await services.get_distributor_by_user_id(db, current_user.id)
    referrals = await services.list_referrals(db, dist.id)
    return [
        schemas.ReferralResponse(
            id=r.id,
            student_id=r.student_id,
            student_name=r.student.full_name if r.student else None,
            student_email=r.student.email if r.student else None,
            course_id=r.course_id,
            course_title=r.course.title if r.course else None,
            created_at=r.created_at,
        )
        for r in referrals
    ]


@router.get("/stats", response_model=schemas.DistributorStatsResponse)
async def get_stats(
    current_user: User = Depends(require_roles(["distributor"])),
    db: AsyncSession = Depends(get_db),
):
    """Get referral statistics for this distributor."""
    dist = await services.get_distributor_by_user_id(db, current_user.id)
    stats = await services.get_distributor_stats(db, dist.id)
    stats["region"] = dist.region
    stats["referral_code"] = dist.referral_code
    return schemas.DistributorStatsResponse(**stats)
