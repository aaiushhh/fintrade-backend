import asyncio
from app.db.database import async_session_maker
from app.modules.courses.services import create_course

async def test():
    async with async_session_maker() as db:
        course = await create_course(db, {'title': 'Test Course', 'price': 100, 'difficulty_level': 'beginner'}, 1)
        print('Created course ID:', course.id)

if __name__ == "__main__":
    asyncio.run(test())
