"""Feedback module — Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    course_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    course_id: Optional[int] = None
    rating: int
    comments: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
