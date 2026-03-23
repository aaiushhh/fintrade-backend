"""Exams module — database models for entrance exams."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class EntranceExam(Base):
    __tablename__ = "entrance_exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    duration_minutes = Column(Integer, default=60)
    passing_score = Column(Float, default=60.0)  # percentage
    max_attempts = Column(Integer, default=0)  # 0 = unlimited (with 30-day restriction)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # relationships
    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EntranceExam {self.title}>"


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("entrance_exams.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="mcq")  # mcq, true_false
    marks = Column(Float, default=1.0)
    order = Column(Integer, default=0)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    exam = relationship("EntranceExam", back_populates="questions")
    options = relationship("ExamOption", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExamQuestion {self.id}>"


class ExamOption(Base):
    __tablename__ = "exam_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    # relationships
    question = relationship("ExamQuestion", back_populates="options")

    def __repr__(self):
        return f"<ExamOption {self.id}>"


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("entrance_exams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    is_submitted = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, nullable=True)

    # relationships
    exam = relationship("EntranceExam", back_populates="attempts")
    answers = relationship("ExamAnswer", back_populates="attempt", cascade="all, delete-orphan")
    result = relationship("ExamResult", back_populates="attempt", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExamAttempt user={self.user_id} exam={self.exam_id}>"


class ExamAnswer(Base):
    __tablename__ = "exam_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("exam_options.id"), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    answered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    attempt = relationship("ExamAttempt", back_populates="answers")

    def __repr__(self):
        return f"<ExamAnswer attempt={self.attempt_id} question={self.question_id}>"


class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(Integer, ForeignKey("entrance_exams.id", ondelete="CASCADE"), nullable=False)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_marks = Column(Float, default=0.0)
    obtained_marks = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # relationships
    attempt = relationship("ExamAttempt", back_populates="result")

    def __repr__(self):
        return f"<ExamResult attempt={self.attempt_id} passed={self.passed}>"
