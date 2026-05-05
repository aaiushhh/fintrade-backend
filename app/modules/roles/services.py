"""Roles module — business logic / services."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.roles.models import AdminPermission
from app.modules.auth.models import User, Role, user_roles
from app.core.security import hash_password


# Map frontend role names to DB enum values
ROLE_MAP = {
    "Super Admin": "super_admin",
    "Content Admin": "content_admin",
    "Finance Admin": "finance_admin",
    "Support Admin": "support_admin",
}

ROLE_MAP_REVERSE = {v: k for k, v in ROLE_MAP.items()}


async def list_admin_users(db: AsyncSession) -> List[dict]:
    """List all admin users with their permissions."""
    result = await db.execute(
        select(AdminPermission).options(selectinload(AdminPermission.user))
    )
    permissions = result.scalars().all()

    admins = []
    for perm in permissions:
        user = perm.user
        if not user:
            continue
        admins.append({
            "id": perm.id,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
            "role": ROLE_MAP_REVERSE.get(perm.admin_role, perm.admin_role),
            "status": perm.status or "Active",
            "permissions": {
                "manage_courses": perm.manage_courses,
                "manage_students": perm.manage_students,
                "manage_payments": perm.manage_payments,
                "manage_content": perm.manage_content,
                "manage_exams": perm.manage_exams,
                "manage_admins": perm.manage_admins,
                "can_view_revenue": perm.can_view_revenue,
            },
            "last_active": perm.last_active,
            "created_at": perm.created_at,
        })
    return admins


async def create_admin_user(db: AsyncSession, data: dict, created_by: int) -> dict:
    """Create a new admin user with role and permissions."""
    from sqlalchemy import select as sel

    # Check if email already exists
    existing = await db.execute(sel(User).where(User.email == data["email"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=data["email"],
        full_name=data["name"],
        phone=data.get("phone"),
        hashed_password=hash_password(data.get("password", "Admin@123")),
        is_active=True,
        is_verified=True,
        created_by=created_by,
    )
    db.add(user)
    await db.flush()

    # Assign admin role
    role_result = await db.execute(sel(Role).where(Role.name == "admin"))
    admin_role = role_result.scalar_one_or_none()
    if admin_role:
        user.roles.append(admin_role)

    # Create permissions
    perms = data.get("permissions", {})
    admin_role_type = ROLE_MAP.get(data.get("role", "Support Admin"), "support_admin")
    permission = AdminPermission(
        user_id=user.id,
        admin_role=admin_role_type,
        manage_courses=perms.get("manage_courses", False),
        manage_students=perms.get("manage_students", False),
        manage_payments=perms.get("manage_payments", False),
        manage_content=perms.get("manage_content", False),
        manage_exams=perms.get("manage_exams", False),
        manage_admins=perms.get("manage_admins", False),
        can_view_revenue=perms.get("can_view_revenue", False),
        status=data.get("status", "Active"),
    )
    db.add(permission)
    await db.commit()
    await db.refresh(user)
    await db.refresh(permission)

    return {
        "id": permission.id,
        "user_id": user.id,
        "name": user.full_name,
        "email": user.email,
        "role": data.get("role", "Support Admin"),
        "status": permission.status,
        "permissions": perms,
        "last_active": permission.last_active,
        "created_at": permission.created_at,
    }


async def update_admin_user(db: AsyncSession, perm_id: int, data: dict) -> dict:
    """Update an admin user's role and permissions."""
    result = await db.execute(
        select(AdminPermission).options(selectinload(AdminPermission.user)).where(AdminPermission.id == perm_id)
    )
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=404, detail="Admin user not found")

    user = perm.user

    # Update user fields
    if data.get("name") and user:
        user.full_name = data["name"]
    if data.get("email") and user:
        user.email = data["email"]

    # Update role
    if data.get("role"):
        perm.admin_role = ROLE_MAP.get(data["role"], perm.admin_role)

    # Update status
    if data.get("status"):
        perm.status = data["status"]

    # Update permissions
    if data.get("permissions"):
        perms = data["permissions"]
        if isinstance(perms, dict):
            for key, value in perms.items():
                if hasattr(perm, key):
                    setattr(perm, key, value)

    await db.commit()
    await db.refresh(perm)
    if user:
        await db.refresh(user)

    return {
        "id": perm.id,
        "user_id": user.id if user else 0,
        "name": user.full_name if user else "",
        "email": user.email if user else "",
        "role": ROLE_MAP_REVERSE.get(perm.admin_role, perm.admin_role),
        "status": perm.status,
        "permissions": {
            "manage_courses": perm.manage_courses,
            "manage_students": perm.manage_students,
            "manage_payments": perm.manage_payments,
            "manage_content": perm.manage_content,
            "manage_exams": perm.manage_exams,
            "manage_admins": perm.manage_admins,
            "can_view_revenue": perm.can_view_revenue,
        },
        "last_active": perm.last_active,
        "created_at": perm.created_at,
    }


async def delete_admin_user(db: AsyncSession, perm_id: int) -> None:
    """Delete an admin permission entry."""
    result = await db.execute(
        select(AdminPermission).where(AdminPermission.id == perm_id)
    )
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if perm.admin_role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot delete Super Admin")

    await db.delete(perm)
    await db.commit()


async def get_role_stats(db: AsyncSession) -> dict:
    """Get admin role statistics."""
    result = await db.execute(select(AdminPermission))
    all_perms = result.scalars().all()

    return {
        "total_admins": len(all_perms),
        "super_admins": sum(1 for p in all_perms if p.admin_role == "super_admin"),
        "active_admins": sum(1 for p in all_perms if p.status == "Active"),
        "role_based_admins": sum(1 for p in all_perms if p.admin_role != "super_admin"),
    }
