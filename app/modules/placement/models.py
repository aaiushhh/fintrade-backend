"""Placement module — database models."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
)

from app.db.database import Base


class PlacementResult(Base):
    __tablename__ = "placement_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    eligible = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    criteria_snapshot = Column(JSON, nullable=True)  # stores the metrics used for evaluation
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PlacementResult user={self.user_id} eligible={self.eligible}>"
