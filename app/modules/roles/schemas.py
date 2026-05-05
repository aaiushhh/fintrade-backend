"""Roles module — Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PermissionsData(BaseModel):
    manage_courses: bool = False
    manage_students: bool = False
    manage_payments: bool = False
    manage_content: bool = False
    manage_exams: bool = False
    manage_admins: bool = False
    can_view_revenue: bool = False


class AdminRoleCreateRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = "Admin@123"
    phone: Optional[str] = None
    role: str = "Support Admin"  # Super Admin, Content Admin, Finance Admin, Support Admin
    status: str = "Active"
    permissions: PermissionsData = PermissionsData()


class AdminRoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[PermissionsData] = None


class AdminRoleResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    role: str
    status: str
    permissions: PermissionsData
    last_active: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminRoleStatsResponse(BaseModel):
    total_admins: int = 0
    super_admins: int = 0
    active_admins: int = 0
    role_based_admins: int = 0


class MessageResponse(BaseModel):
    message: str
