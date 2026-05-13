import asyncio
import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import select
from app.db.session import SessionLocal
from app.modules.exams.models import EntranceExam, CourseExam

async def check():
    async with SessionLocal() as db:
        res1 = await db.execute(select(EntranceExam))
        ent = res1.scalars().all()
        res2 = await db.execute(select(CourseExam))
        cou = res2.scalars().all()
        print(f"--- Entrance Exams ({len(ent)}) ---")
        for e in ent:
            print(f"  ID: {e.id}, Title: {e.title}, Active: {e.is_active}")
        print(f"--- Course Exams ({len(cou)}) ---")
        for e in cou:
            print(f"  ID: {e.id}, Title: {e.title}, Active: {e.is_active}")

if __name__ == "__main__":
    asyncio.run(check())
