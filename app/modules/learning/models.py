"""Learning module — database models."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class LessonCompletion(Base):
    """Tracks which specific lessons a user has completed."""
    __tablename__ = "lesson_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<LessonCompletion user={self.user_id} lesson={self.lesson_id}>"
