"""Exams module — Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Admin: Create exam / question / option ──────────────────────────
class ExamOptionCreate(BaseModel):
    option_text: str = Field(..., min_length=1)
    is_correct: bool = False
    order: int = 0


class ExamQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)
    question_type: str = "mcq"
    marks: float = 1.0
    order: int = 0
    explanation: Optional[str] = None
    options: List[ExamOptionCreate] = []


class EntranceExamCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    course_id: int
    duration_minutes: int = 60
    passing_score: float = 60.0
    is_active: bool = True
    questions: List[ExamQuestionCreate] = []


# ── Response schemas ─────────────────────────────────────────────────
class ExamOptionResponse(BaseModel):
    id: int
    option_text: str
    order: int
    # NOTE: is_correct is intentionally excluded for students

    model_config = {"from_attributes": True}


class ExamQuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: str
    marks: float
    order: int
    options: List[ExamOptionResponse] = []

    model_config = {"from_attributes": True}


class EntranceExamResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    course_id: int
    duration_minutes: int
    passing_score: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AttemptStartResponse(BaseModel):
    attempt_id: int
    exam_id: int
    started_at: datetime
    duration_minutes: int
    total_questions: int

    model_config = {"from_attributes": True}


# ── Answer submission ────────────────────────────────────────────────
class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: int


class ExamSubmitRequest(BaseModel):
    attempt_id: int
    answers: List[AnswerSubmit] = []


# ── Result ───────────────────────────────────────────────────────────
class ExamResultResponse(BaseModel):
    id: int
    attempt_id: int
    total_questions: int
    correct_answers: int
    total_marks: float
    obtained_marks: float
    percentage: float
    passed: bool
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


# ── Phase 2 Schemas ───────────────────────────────────────────────────

class CourseExamResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    course_id: int
    module_id: Optional[int] = None
    exam_type: str
    duration_minutes: int
    passing_score: float
    max_attempts: int
    is_active: bool

    model_config = {"from_attributes": True}

class MonthlyExamResponse(BaseModel):
    id: int
    course_id: int
    month_number: int
    exam: Optional[CourseExamResponse] = None

    model_config = {"from_attributes": True}

class ExamStartRequest(BaseModel):
    device_id: str

class AttemptCourseStartResponse(BaseModel):
    attempt_id: int
    exam_id: int
    started_at: datetime
    duration_minutes: int
    device_id: Optional[str] = None

    model_config = {"from_attributes": True}

class ExamPaymentRequest(BaseModel):
    exam_id: int
    amount: float = 50.0

class ExamViolationRequest(BaseModel):
    attempt_id: int
    violation_type: str

class CameraStatusRequest(BaseModel):
    attempt_id: int
    camera_on: bool

class SessionCloseRequest(BaseModel):
    attempt_id: int
