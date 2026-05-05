"""Settings module — Pydantic schemas."""

from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel


class SettingResponse(BaseModel):
    id: int
    key: str
    value: Optional[str] = None
    category: str = "general"
    label: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SettingUpdateRequest(BaseModel):
    value: str


class BulkSettingUpdateRequest(BaseModel):
    settings: Dict[str, str]  # key -> value pairs


class SettingsGroupedResponse(BaseModel):
    general: List[SettingResponse] = []
    simulator: List[SettingResponse] = []
    exam: List[SettingResponse] = []
    payment: List[SettingResponse] = []


class MessageResponse(BaseModel):
    message: str
