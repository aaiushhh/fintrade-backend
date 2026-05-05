"""Roles module — API routes."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.db.database import get_db
from app.modules.auth.models import User
from app.modules.roles import schemas, services

router = APIRouter(prefix="/admin/roles", tags=["Admin Roles"])


@router.get("", response_model=List[schemas.AdminRoleResponse])
async def list_admin_roles(
    _admin: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """List all admin users with permissions."""
    admins = await services.list_admin_users(db)
    return admins


@router.post("", response_model=schemas.AdminRoleResponse, status_code=201)
async def create_admin_role(
    body: schemas.AdminRoleCreateRequest,
    admin: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new admin user with role and permissions."""
    data = body.model_dump()
    if body.permissions:
        data["permissions"] = body.permissions.model_dump()
    result = await services.create_admin_user(db, data, created_by=admin.id)
    return result


@router.put("/{perm_id}", response_model=schemas.AdminRoleResponse)
async def update_admin_role(
    perm_id: int,
    body: schemas.AdminRoleUpdateRequest,
    _admin: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Update admin user role and permissions."""
    data = body.model_dump(exclude_unset=True)
    if body.permissions:
        data["permissions"] = body.permissions.model_dump()
    result = await services.update_admin_user(db, perm_id, data)
    return result


@router.delete("/{perm_id}", response_model=schemas.MessageResponse)
async def delete_admin_role(
    perm_id: int,
    _admin: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Remove admin user (cannot remove Super Admin)."""
    await services.delete_admin_user(db, perm_id)
    return schemas.MessageResponse(message="Admin user removed successfully")


@router.get("/stats", response_model=schemas.AdminRoleStatsResponse)
async def role_stats(
    _admin: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Get admin role statistics."""
    stats = await services.get_role_stats(db)
    return schemas.AdminRoleStatsResponse(**stats)
