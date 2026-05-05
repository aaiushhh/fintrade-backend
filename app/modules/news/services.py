"""News module — business logic / services."""

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.news.models import NewsArticle


async def list_published_news(db: AsyncSession, skip: int = 0, limit: int = 20) -> List[NewsArticle]:
    """List published news articles (public)."""
    result = await db.execute(
        select(NewsArticle)
        .where(NewsArticle.status == "published")
        .order_by(NewsArticle.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_article(db: AsyncSession, article_id: int) -> NewsArticle:
    """Get a single news article."""
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    # Increment view count
    article.views_count += 1
    await db.commit()
    await db.refresh(article)
    return article


async def list_all_news(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[NewsArticle]:
    """List all news articles including drafts (admin)."""
    result = await db.execute(
        select(NewsArticle)
        .order_by(NewsArticle.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def create_article(db: AsyncSession, data: dict, created_by: int) -> NewsArticle:
    """Create a new news article."""
    article = NewsArticle(created_by=created_by, **data)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article


async def update_article(db: AsyncSession, article_id: int, data: dict) -> NewsArticle:
    """Update an existing article."""
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    for key, value in data.items():
        if value is not None and hasattr(article, key):
            setattr(article, key, value)

    await db.commit()
    await db.refresh(article)
    return article


async def delete_article(db: AsyncSession, article_id: int) -> None:
    """Delete an article."""
    result = await db.execute(
        select(NewsArticle).where(NewsArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await db.delete(article)
    await db.commit()


async def get_news_stats(db: AsyncSession) -> dict:
    """Get news statistics."""
    result = await db.execute(select(NewsArticle))
    articles = result.scalars().all()

    return {
        "total_articles": len(articles),
        "youtube_count": sum(1 for a in articles if a.video_type == "youtube"),
        "uploaded_count": sum(1 for a in articles if a.video_type == "uploaded"),
        "total_views": sum(a.views_count for a in articles),
        "draft_count": sum(1 for a in articles if a.status == "draft"),
    }
