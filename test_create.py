import asyncio
from app.db.database import AsyncSessionLocal
from app.modules.courses.services import create_course
from app.modules.auth.models import User
async def run():
    async with AsyncSessionLocal() as db:
        try:
            course = await create_course(db, {"title": "Test Course 456", "description": "test"}, 1)
            await db.commit()
            print("Course created:", course.id)
            from app.modules.courses.schemas import CourseDetailResponse
            res = CourseDetailResponse.model_validate(course)
            print("Validation successful!")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
