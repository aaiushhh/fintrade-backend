import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select
from datetime import datetime, timezone

from app.modules.lectures.models import Lecture

# Provide connection directly to the test db or the actual running db?
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/lms_db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def test_create_lecture():
    async with AsyncSessionLocal() as db:
        lecture = Lecture(
            title="test manual",
            course_id=1,  # Assuming course 1 exists
            instructor_id=1, # Assuming user 1 exists
            scheduled_at=datetime.now(timezone.utc),
            duration_minutes=60,
        )
        db.add(lecture)
        await db.flush()
        # Does flush give it an ID?
        print(f"ID after flush: {lecture.id}")
        
        # Load with relationship inside the same transaction
        query = select(Lecture).options(selectinload(Lecture.recordings)).filter(Lecture.id == lecture.id)
        result = await db.execute(query)
        lecture_out = result.scalar_one()
        print(f"Recordings: {lecture_out.recordings}")
        await db.commit()
        print("Success")

if __name__ == "__main__":
    asyncio.run(test_create_lecture())
