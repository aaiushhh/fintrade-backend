"""Placement module — Pydantic schemas."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class PlacementStatusResponse(BaseModel):
    evaluated: bool
    eligible: Optional[bool] = None
    score: Optional[float] = None
    criteria: Optional[Any] = None
    evaluated_at: Optional[datetime] = None


class PlacementEvaluateResponse(BaseModel):
    eligible: bool
    score: float
    criteria: Any
    message: str

    model_config = {"from_attributes": True}
