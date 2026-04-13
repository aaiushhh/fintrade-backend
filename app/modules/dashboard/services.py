"""Dashboard module — service layer for announcements and advertisements."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.models import Announcement, Advertisement


# ═════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS
# ═════════════════════════════════════════════════════════════════════

async def create_announcement(db: AsyncSession, admin_id: int, data: dict) -> Announcement:
    """Create a new announcement (admin only)."""
    ann = Announcement(
        title=data["title"],
        content=data["content"],
        priority=data.get("priority", "normal"),
        is_active=data.get("is_active", True),
        expires_at=data.get("expires_at"),
        created_by=admin_id,
    )
    db.add(ann)
    await db.flush()
    await db.refresh(ann)
    return ann


async def update_announcement(db: AsyncSession, ann_id: int, data: dict) -> Announcement:
    """Update an existing announcement."""
    ann = await db.get(Announcement, ann_id)
    if ann is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    for key, value in data.items():
        if value is not None:
            setattr(ann, key, value)

    await db.flush()
    await db.refresh(ann)
    return ann


async def delete_announcement(db: AsyncSession, ann_id: int) -> None:
    """Delete an announcement."""
    ann = await db.get(Announcement, ann_id)
    if ann is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await db.delete(ann)
    await db.flush()


async def list_announcements_admin(db: AsyncSession) -> List[Announcement]:
    """List all announcements (admin view — includes inactive)."""
    result = await db.execute(
        select(Announcement).order_by(Announcement.created_at.desc())
    )
    return list(result.scalars().all())


async def list_active_announcements(db: AsyncSession) -> List[Announcement]:
    """List active, non-expired announcements (student view)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Announcement)
        .where(
            Announcement.is_active == True,
        )
        .order_by(Announcement.priority.desc(), Announcement.published_at.desc())
    )
    announcements = result.scalars().all()
    # Filter expired in Python (nullable expires_at)
    return [a for a in announcements if a.expires_at is None or a.expires_at > now]


# ═════════════════════════════════════════════════════════════════════
# ADVERTISEMENTS
# ═════════════════════════════════════════════════════════════════════

async def create_advertisement(db: AsyncSession, admin_id: int, data: dict) -> Advertisement:
    """Create a new advertisement (admin only)."""
    ad = Advertisement(
        title=data["title"],
        description=data.get("description"),
        image_url=data.get("image_url"),
        link_url=data.get("link_url"),
        placement=data.get("placement", "dashboard"),
        is_active=data.get("is_active", True),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        created_by=admin_id,
    )
    db.add(ad)
    await db.flush()
    await db.refresh(ad)
    return ad


async def update_advertisement(db: AsyncSession, ad_id: int, data: dict) -> Advertisement:
    """Update an existing advertisement."""
    ad = await db.get(Advertisement, ad_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    for key, value in data.items():
        if value is not None:
            setattr(ad, key, value)

    await db.flush()
    await db.refresh(ad)
    return ad


async def delete_advertisement(db: AsyncSession, ad_id: int) -> None:
    """Delete an advertisement."""
    ad = await db.get(Advertisement, ad_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    await db.delete(ad)
    await db.flush()


async def list_advertisements_admin(db: AsyncSession) -> List[Advertisement]:
    """List all advertisements (admin view — includes inactive)."""
    result = await db.execute(
        select(Advertisement).order_by(Advertisement.created_at.desc())
    )
    return list(result.scalars().all())


async def list_active_advertisements(db: AsyncSession, placement: Optional[str] = None) -> List[Advertisement]:
    """List active advertisements within date range (student view)."""
    now = datetime.now(timezone.utc)
    query = select(Advertisement).where(Advertisement.is_active == True)

    if placement:
        query = query.where(Advertisement.placement == placement)

    result = await db.execute(query.order_by(Advertisement.created_at.desc()))
    ads = result.scalars().all()
    # Filter by date range in Python (nullable fields)
    return [
        a for a in ads
        if (a.start_date is None or a.start_date <= now)
        and (a.end_date is None or a.end_date > now)
    ]
