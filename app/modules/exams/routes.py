"""Exams module — API routes."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.modules.auth.models import User
from app.modules.exams import schemas, services

router = APIRouter(prefix="/exams", tags=["Entrance Exams"])


@router.get("/entrance", response_model=List[schemas.EntranceExamResponse])
async def list_entrance_exams(db: AsyncSession = Depends(get_db)):
    """List all active entrance exams."""
    exams = await services.get_entrance_exams(db)
    return [schemas.EntranceExamResponse.model_validate(e) for e in exams]


@router.post("/start", response_model=schemas.AttemptStartResponse)
async def start_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new exam attempt (enforces 30-day restriction)."""
    result = await services.start_exam(db, current_user.id, exam_id)
    return result


@router.get("/questions", response_model=List[schemas.ExamQuestionResponse])
async def get_questions(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get questions for the current active attempt (correct answers hidden)."""
    questions = await services.get_exam_questions(db, current_user.id, exam_id)
    return [schemas.ExamQuestionResponse.model_validate(q) for q in questions]


@router.post("/answer", response_model=schemas.MessageResponse)
async def save_answer(
    body: schemas.AnswerSubmit,
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save an individual answer during the exam."""
    await services.save_answer(
        db, current_user.id, attempt_id, body.question_id, body.selected_option_id
    )
    return schemas.MessageResponse(message="Answer saved")


@router.post("/submit", response_model=schemas.ExamResultResponse)
async def submit_exam(
    body: schemas.ExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit the exam, auto-evaluate, and return the result."""
    answers = [{"question_id": a.question_id, "selected_option_id": a.selected_option_id} for a in body.answers]
    result = await services.submit_exam(db, current_user.id, body.attempt_id, answers)
    return schemas.ExamResultResponse.model_validate(result)


@router.get("/result", response_model=schemas.ExamResultResponse)
async def get_result(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent exam result."""
    result = await services.get_exam_result(db, current_user.id, exam_id)
    return schemas.ExamResultResponse.model_validate(result)
