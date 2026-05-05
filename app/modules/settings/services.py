"""Settings module — business logic / services."""

from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.models import PlatformSetting


# Default settings to seed if table is empty
DEFAULT_SETTINGS = [
    {"key": "platform_name", "value": "FinTrade", "category": "general", "label": "Platform Name"},
    {"key": "support_email", "value": "support@fintrade.com", "category": "general", "label": "Support Email"},
    {"key": "default_course_price", "value": "25000", "category": "payment", "label": "Default Course Price (₹)"},
    {"key": "exam_retake_fee", "value": "300", "category": "payment", "label": "Exam Retake Fee (₹)"},
    {"key": "starting_capital", "value": "500000", "category": "simulator", "label": "Starting Capital (₹)"},
    {"key": "daily_loss_limit", "value": "10000", "category": "simulator", "label": "Daily Loss Limit (₹)"},
    {"key": "passing_score", "value": "60", "category": "exam", "label": "Passing Score (%)"},
    {"key": "max_attempts", "value": "3", "category": "exam", "label": "Max Attempts Per Exam"},
]


async def ensure_defaults(db: AsyncSession) -> None:
    """Seed default settings if table is empty."""
    result = await db.execute(select(PlatformSetting))
    existing = result.scalars().all()
    if existing:
        return

    for s in DEFAULT_SETTINGS:
        db.add(PlatformSetting(**s))
    await db.commit()


async def get_public_settings(db: AsyncSession) -> List[PlatformSetting]:
    """Get settings that are safe for public (general + payment category)."""
    await ensure_defaults(db)
    result = await db.execute(
        select(PlatformSetting).where(
            PlatformSetting.category.in_(["general", "payment"])
        )
    )
    return result.scalars().all()


async def get_all_settings(db: AsyncSession) -> Dict[str, List[PlatformSetting]]:
    """Get all settings grouped by category (admin)."""
    await ensure_defaults(db)
    result = await db.execute(
        select(PlatformSetting).order_by(PlatformSetting.category, PlatformSetting.key)
    )
    settings = result.scalars().all()

    grouped = {"general": [], "simulator": [], "exam": [], "payment": []}
    for s in settings:
        category = s.category or "general"
        if category in grouped:
            grouped[category].append(s)
        else:
            grouped["general"].append(s)
    return grouped


async def update_setting(db: AsyncSession, key: str, value: str, admin_id: int) -> PlatformSetting:
    """Update a single setting by key."""
    result = await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    setting.value = value
    setting.updated_by = admin_id
    await db.commit()
    await db.refresh(setting)
    return setting


async def bulk_update_settings(db: AsyncSession, settings: Dict[str, str], admin_id: int) -> int:
    """Update multiple settings at once. Returns count of updated settings."""
    updated = 0
    for key, value in settings.items():
        result = await db.execute(
            select(PlatformSetting).where(PlatformSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
            setting.updated_by = admin_id
            updated += 1

    await db.commit()
    return updated
