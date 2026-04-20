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

class TrendData(BaseModel):
    month: str
    avgScore: int
    passRate: int

class TopicData(BaseModel):
    topic: str
    struggles: int

class ModuleData(BaseModel):
    module: str
    completion: int

class DistributionData(BaseModel):
    category: str
    value: int

class FacultyReportsResponse(BaseModel):
    avg_class_score: int
    pass_rate: int
    completion_rate: int
    at_risk_students: int
    performance_trend: List[TrendData]
    weak_topics: List[TopicData]
    module_completion: List[ModuleData]
    student_distribution: List[DistributionData]
