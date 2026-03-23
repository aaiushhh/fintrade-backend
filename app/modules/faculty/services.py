"""Faculty module — service layer."""

from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.courses.models import Course, CourseEnrollment, CourseModule, Lesson
from app.modules.lectures.models import Lecture
from app.modules.auth.models import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_faculty_courses(db: AsyncSession, faculty_id: int) -> List[Course]:
    """Get all courses created by this faculty member."""
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
        .where(Course.created_by == faculty_id)
        .order_by(Course.created_at.desc())
    )
    return list(result.scalars().all())


async def create_faculty_lesson(db: AsyncSession, data: dict, faculty_id: int) -> Lesson:
    """Faculty creates a lesson — must own the parent course."""
    module = await db.get(CourseModule, data["module_id"])
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    course = await db.get(Course, module.course_id)
    if course is None or course.created_by != faculty_id:
        raise HTTPException(status_code=403, detail="You do not own this course")

    lesson = Lesson(
        module_id=data["module_id"],
        title=data["title"],
        content=data.get("content"),
        content_type=data.get("content_type", "text"),
        video_url=data.get("video_url"),
        duration_minutes=data.get("duration_minutes"),
        order=data.get("order", 0),
        is_published=data.get("is_published", False),
    )
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)
    logger.info("faculty_lesson_created", lesson_id=lesson.id, faculty_id=faculty_id)
    return lesson


async def create_faculty_lecture(db: AsyncSession, data: dict, faculty_id: int) -> Lecture:
    """Faculty creates a lecture — they are automatically set as instructor."""
    course = await db.get(Course, data["course_id"])
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    lecture = Lecture(
        title=data["title"],
        description=data.get("description"),
        course_id=data["course_id"],
        instructor_id=faculty_id,
        meeting_link=data.get("meeting_link"),
        scheduled_at=data["scheduled_at"],
        duration_minutes=data.get("duration_minutes", 60),
        max_participants=data.get("max_participants", 0),
    )
    db.add(lecture)
    await db.commit()
    
    # Reload with relationships
    query = select(Lecture).options(selectinload(Lecture.recordings)).filter(Lecture.id == lecture.id)
    result = await db.execute(query)
    lecture = result.scalar_one()

    logger.info("faculty_lecture_created", lecture_id=lecture.id, faculty_id=faculty_id)
    return lecture


async def get_faculty_students(db: AsyncSession, faculty_id: int) -> List[dict]:
    """Get students enrolled in courses created by this faculty."""
    # Get faculty course IDs
    course_result = await db.execute(
        select(Course.id).where(Course.created_by == faculty_id)
    )
    course_ids = [row[0] for row in course_result.all()]
    if not course_ids:
        return []

    # Get enrollments for those courses
    result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.course))
        .where(CourseEnrollment.course_id.in_(course_ids))
        .order_by(CourseEnrollment.enrolled_at.desc())
    )
    enrollments = list(result.scalars().all())

    # Get student users
    student_ids = [e.user_id for e in enrollments]
    if not student_ids:
        return []

    user_result = await db.execute(
        select(User).where(User.id.in_(student_ids))
    )
    users_map = {u.id: u for u in user_result.scalars().all()}

    return [
        {
            "student_id": e.user_id,
            "student_name": users_map[e.user_id].full_name if e.user_id in users_map else "Unknown",
            "student_email": users_map[e.user_id].email if e.user_id in users_map else "",
            "course_id": e.course_id,
            "course_title": e.course.title if e.course else "",
            "enrolled_at": e.enrolled_at,
        }
        for e in enrollments
    ]
