"""Faculty module — Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.courses.schemas import LessonCreate, LessonResponse, CourseListResponse
from app.modules.lectures.schemas import LectureCreate, LectureResponse


class FacultyStudentResponse(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    course_id: int
    course_title: str
    enrolled_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
