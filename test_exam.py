import asyncio
from app.db.database import AsyncSessionLocal
from app.modules.exams.services import create_exam
from app.modules.auth.models import User
from app.modules.courses.models import Course
async def run():
    async with AsyncSessionLocal() as db:
        try:
            data = {
                "title": "Test Exam",
                "course_id": 1,
                "duration_minutes": 60,
                "passing_score": 60.0,
                "is_active": True,
                "questions": [
                    {
                        "question_text": "Sample Q?",
                        "options": [
                            {"option_text": "A", "is_correct": True}
                        ]
                    }
                ]
            }
            exam = await create_exam(db, data)
            await db.commit()
            print("Exam created:", exam.id)
            from app.modules.exams.schemas import EntranceExamResponse
            res = EntranceExamResponse.model_validate(exam)
            print("Validation successful!")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
