"""Exams module — service layer with 30-day reattempt restriction."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.exams.models import (
    EntranceExam,
    ExamAnswer,
    ExamAttempt,
    ExamOption,
    ExamQuestion,
    ExamResult,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

REATTEMPT_DAYS = 30


# ── Helpers ──────────────────────────────────────────────────────────
async def _check_reattempt_allowed(db: AsyncSession, user_id: int, exam_id: int) -> None:
    """Raise 403 if the student failed and must wait 30 days."""
    # Find the most recent completed attempt
    result = await db.execute(
        select(ExamAttempt)
        .where(
            ExamAttempt.user_id == user_id,
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.is_submitted == True,  # noqa: E712
        )
        .order_by(ExamAttempt.submitted_at.desc())
        .limit(1)
    )
    last_attempt = result.scalar_one_or_none()
    if last_attempt is None:
        return  # first attempt — allowed

    # Check if the last attempt passed
    result_row = await db.execute(
        select(ExamResult).where(ExamResult.attempt_id == last_attempt.id)
    )
    exam_result = result_row.scalar_one_or_none()

    if exam_result and exam_result.passed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already passed this exam.",
        )

    # Failed — enforce 30-day wait
    if last_attempt.submitted_at:
        next_allowed = last_attempt.submitted_at + timedelta(days=REATTEMPT_DAYS)
        if datetime.now(timezone.utc) < next_allowed:
            days_left = (next_allowed - datetime.now(timezone.utc)).days
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You must wait {days_left} more day(s) before reattempting. Next attempt allowed after {next_allowed.strftime('%Y-%m-%d')}.",
            )


# ── Admin: create exam ──────────────────────────────────────────────
async def create_exam(db: AsyncSession, data: dict) -> EntranceExam:
    """Create an entrance exam with questions and options."""
    exam = EntranceExam(
        title=data["title"],
        description=data.get("description"),
        course_id=data["course_id"],
        duration_minutes=data.get("duration_minutes", 60),
        passing_score=data.get("passing_score", 60.0),
        is_active=data.get("is_active", True),
    )
    db.add(exam)
    await db.flush()

    for q_data in data.get("questions", []):
        question = ExamQuestion(
            exam_id=exam.id,
            question_text=q_data["question_text"],
            question_type=q_data.get("question_type", "mcq"),
            marks=q_data.get("marks", 1.0),
            order=q_data.get("order", 0),
            explanation=q_data.get("explanation"),
        )
        db.add(question)
        await db.flush()

        for opt_data in q_data.get("options", []):
            option = ExamOption(
                question_id=question.id,
                option_text=opt_data["option_text"],
                is_correct=opt_data.get("is_correct", False),
                order=opt_data.get("order", 0),
            )
            db.add(option)

    await db.flush()
    await db.refresh(exam)
    logger.info("exam_created", exam_id=exam.id, title=exam.title)
    return exam


async def add_questions_to_exam(db: AsyncSession, exam_id: int, questions_data: list) -> None:
    """Add questions to an existing exam (admin)."""
    exam = await db.get(EntranceExam, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")

    for q_data in questions_data:
        question = ExamQuestion(
            exam_id=exam_id,
            question_text=q_data["question_text"],
            question_type=q_data.get("question_type", "mcq"),
            marks=q_data.get("marks", 1.0),
            order=q_data.get("order", 0),
            explanation=q_data.get("explanation"),
        )
        db.add(question)
        await db.flush()

        for opt_data in q_data.get("options", []):
            option = ExamOption(
                question_id=question.id,
                option_text=opt_data["option_text"],
                is_correct=opt_data.get("is_correct", False),
                order=opt_data.get("order", 0),
            )
            db.add(option)

    await db.flush()
    logger.info("questions_added", exam_id=exam_id, count=len(questions_data))


# ── Student: get available entrance exams ────────────────────────────
async def get_entrance_exams(db: AsyncSession) -> List[EntranceExam]:
    """List all active entrance exams."""
    result = await db.execute(
        select(EntranceExam)
        .where(EntranceExam.is_active == True)  # noqa: E712
        .order_by(EntranceExam.created_at.desc())
    )
    return list(result.scalars().all())


# ── Student: start exam ─────────────────────────────────────────────
async def start_exam(db: AsyncSession, user_id: int, exam_id: int) -> dict:
    """Create a new attempt after checking eligibility."""
    exam = await db.get(EntranceExam, exam_id)
    if exam is None or not exam.is_active:
        raise HTTPException(status_code=404, detail="Exam not found or inactive")

    # Check in-progress attempt
    result = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.user_id == user_id,
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.is_submitted == False,  # noqa: E712
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an in-progress attempt for this exam.",
        )

    await _check_reattempt_allowed(db, user_id, exam_id)

    # Count questions
    q_count_result = await db.execute(
        select(func.count(ExamQuestion.id)).where(ExamQuestion.exam_id == exam_id)
    )
    total_questions = q_count_result.scalar() or 0

    attempt = ExamAttempt(exam_id=exam_id, user_id=user_id)
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    logger.info("exam_started", user_id=user_id, exam_id=exam_id, attempt_id=attempt.id)

    return {
        "attempt_id": attempt.id,
        "exam_id": exam_id,
        "started_at": attempt.started_at,
        "duration_minutes": exam.duration_minutes,
        "total_questions": total_questions,
    }


# ── Student: get questions for an attempt ────────────────────────────
async def get_exam_questions(db: AsyncSession, user_id: int, exam_id: int) -> List[ExamQuestion]:
    """Return questions with options (without correct-answer flags) for the student."""
    # Verify active attempt exists
    result = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.user_id == user_id,
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.is_submitted == False,  # noqa: E712
        )
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=400, detail="No active attempt found. Start the exam first.")

    q_result = await db.execute(
        select(ExamQuestion)
        .options(selectinload(ExamQuestion.options))
        .where(ExamQuestion.exam_id == exam_id)
        .order_by(ExamQuestion.order)
    )
    return list(q_result.scalars().all())


# ── Student: save individual answer ─────────────────────────────────
async def save_answer(
    db: AsyncSession, user_id: int, attempt_id: int, question_id: int, selected_option_id: int
) -> ExamAnswer:
    """Save or update an answer for a question within an attempt."""
    # Verify attempt belongs to user and is not submitted
    attempt = await db.get(ExamAttempt, attempt_id)
    if attempt is None or attempt.user_id != user_id or attempt.is_submitted:
        raise HTTPException(status_code=400, detail="Invalid or submitted attempt")

    # Check if answer already exists
    result = await db.execute(
        select(ExamAnswer).where(
            ExamAnswer.attempt_id == attempt_id,
            ExamAnswer.question_id == question_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.selected_option_id = selected_option_id
        existing.answered_at = datetime.now(timezone.utc)
        await db.flush()
        return existing

    answer = ExamAnswer(
        attempt_id=attempt_id,
        question_id=question_id,
        selected_option_id=selected_option_id,
    )
    db.add(answer)
    await db.flush()
    return answer


# ── Student: submit exam and evaluate ────────────────────────────────
async def submit_exam(db: AsyncSession, user_id: int, attempt_id: int, answers: list) -> ExamResult:
    """Submit the exam, evaluate answers, and generate result."""
    attempt = await db.get(ExamAttempt, attempt_id)
    if attempt is None or attempt.user_id != user_id:
        raise HTTPException(status_code=400, detail="Invalid attempt")
    if attempt.is_submitted:
        raise HTTPException(status_code=409, detail="Exam already submitted")

    # Save any remaining answers
    for ans in answers:
        await save_answer(db, user_id, attempt_id, ans["question_id"], ans["selected_option_id"])

    # Get all questions for this exam
    q_result = await db.execute(
        select(ExamQuestion)
        .options(selectinload(ExamQuestion.options))
        .where(ExamQuestion.exam_id == attempt.exam_id)
    )
    questions = list(q_result.scalars().all())

    # Get all student answers for this attempt
    a_result = await db.execute(
        select(ExamAnswer).where(ExamAnswer.attempt_id == attempt_id)
    )
    student_answers = {a.question_id: a for a in a_result.scalars().all()}

    # Evaluate
    total_marks = 0.0
    obtained_marks = 0.0
    correct_count = 0

    for question in questions:
        total_marks += question.marks
        student_answer = student_answers.get(question.id)
        if student_answer and student_answer.selected_option_id:
            # Find the correct option
            correct_option = next((o for o in question.options if o.is_correct), None)
            if correct_option and student_answer.selected_option_id == correct_option.id:
                student_answer.is_correct = True
                obtained_marks += question.marks
                correct_count += 1
            else:
                student_answer.is_correct = False

    percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0.0

    # Get passing score
    exam = await db.get(EntranceExam, attempt.exam_id)
    passed = percentage >= exam.passing_score

    # Mark attempt as submitted
    now = datetime.now(timezone.utc)
    attempt.is_submitted = True
    attempt.submitted_at = now
    if attempt.started_at:
        attempt.time_spent_seconds = int((now - attempt.started_at).total_seconds())

    # Create result
    exam_result = ExamResult(
        attempt_id=attempt_id,
        user_id=user_id,
        exam_id=attempt.exam_id,
        total_questions=len(questions),
        correct_answers=correct_count,
        total_marks=total_marks,
        obtained_marks=obtained_marks,
        percentage=round(percentage, 2),
        passed=passed,
    )
    db.add(exam_result)
    await db.flush()
    await db.refresh(exam_result)

    logger.info(
        "exam_submitted",
        user_id=user_id,
        attempt_id=attempt_id,
        percentage=percentage,
        passed=passed,
    )
    return exam_result


# ── Student: get result ─────────────────────────────────────────────
async def get_exam_result(db: AsyncSession, user_id: int, exam_id: int) -> Optional[ExamResult]:
    """Get the most recent exam result for a user."""
    result = await db.execute(
        select(ExamResult)
        .where(ExamResult.user_id == user_id, ExamResult.exam_id == exam_id)
        .order_by(ExamResult.evaluated_at.desc())
        .limit(1)
    )
    exam_result = result.scalar_one_or_none()
    if exam_result is None:
        raise HTTPException(status_code=404, detail="No exam result found")
    return exam_result


# ── Phase 2: Course & Monthly Exams ───────────────────────────────────

from app.modules.exams.models import (
    CourseExam, MonthlyExam, ExamPayment, CourseExamAttempt, ExamViolation
)

async def get_monthly_exams(db: AsyncSession, user_id: int) -> List[MonthlyExam]:
    """Fetch all monthly exams."""
    result = await db.execute(
        select(MonthlyExam).options(selectinload(MonthlyExam.exam))
    )
    return list(result.scalars().all())

async def process_exam_payment(db: AsyncSession, user_id: int, exam_id: int, amount: float) -> ExamPayment:
    """Mock payment for reattempt."""
    payment = ExamPayment(user_id=user_id, exam_id=exam_id, amount=amount, status="paid")
    db.add(payment)
    await db.flush()
    return payment

async def verify_course_exam_attempt_allowed(db: AsyncSession, user_id: int, exam_id: int) -> None:
    # Check if a failed attempt exists that requires payment
    result = await db.execute(
        select(CourseExamAttempt)
        .where(CourseExamAttempt.user_id == user_id, CourseExamAttempt.exam_id == exam_id, CourseExamAttempt.is_submitted == True)
        .order_by(CourseExamAttempt.submitted_at.desc())
        .limit(1)
    )
    last_attempt = result.scalar_one_or_none()
    if not last_attempt:
        return # First attempt
        
    # Check if passed
    if last_attempt.result and last_attempt.result.passed:
        raise HTTPException(status_code=409, detail="Exam already passed.")
        
    # Check payment
    pay_result = await db.execute(
        select(ExamPayment).where(ExamPayment.user_id == user_id, ExamPayment.exam_id == exam_id, ExamPayment.status == "paid")
    )
    if not pay_result.scalars().first():
        raise HTTPException(status_code=402, detail="Payment required to reattempt this exam.")

async def start_course_exam(db: AsyncSession, user_id: int, exam_id: int, device_id: str) -> dict:
    exam = await db.get(CourseExam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
        
    await verify_course_exam_attempt_allowed(db, user_id, exam_id)
    
    attempt = CourseExamAttempt(user_id=user_id, exam_id=exam_id, device_id=device_id)
    db.add(attempt)
    await db.flush()
    
    return {
        "attempt_id": attempt.id,
        "exam_id": exam_id,
        "started_at": attempt.started_at,
        "duration_minutes": exam.duration_minutes,
        "device_id": attempt.device_id
    }

async def log_exam_violation(db: AsyncSession, user_id: int, attempt_id: int, violation_type: str) -> None:
    violation = ExamViolation(attempt_id=attempt_id, violation_type=violation_type)
    db.add(violation)
    await db.flush()

async def close_exam_session(db: AsyncSession, user_id: int, attempt_id: int) -> None:
    attempt = await db.get(CourseExamAttempt, attempt_id)
    if attempt and not attempt.is_submitted and attempt.user_id == user_id:
        attempt.is_submitted = True
        attempt.submitted_at = datetime.now(timezone.utc)
        await db.flush()


# ── Skill-Based Result Analysis ──────────────────────────────────────

from app.modules.exams.models import CategoryScore

async def get_skill_analysis(db: AsyncSession, user_id: int) -> dict:
    """Analyse user's category scores and return strong/weak areas."""
    result = await db.execute(
        select(CategoryScore).where(CategoryScore.user_id == user_id)
    )
    scores = list(result.scalars().all())

    if not scores:
        return {"strong_areas": [], "weak_areas": [], "suggestions": ["Complete exams to see your skill analysis."]}

    scored = []
    for s in scores:
        pct = (s.score / s.max_score * 100) if s.max_score > 0 else 0
        scored.append({
            "category": s.category,
            "score": s.score,
            "max_score": s.max_score,
            "percentage": round(pct, 1),
        })

    scored.sort(key=lambda x: x["percentage"], reverse=True)

    strong = [s for s in scored if s["percentage"] >= 70]
    weak = [s for s in scored if s["percentage"] < 70]

    suggestions = []
    for w in weak:
        suggestions.append(f"Improve your {w['category']} skills — currently at {w['percentage']}%.")
    if not weak:
        suggestions.append("Great job! You're performing well across all categories.")

    return {"strong_areas": strong, "weak_areas": weak, "suggestions": suggestions}

