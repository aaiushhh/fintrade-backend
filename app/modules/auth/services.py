"""Auth module — business logic / service layer."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.modules.auth.models import Role, Session, User
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_or_create_role(db: AsyncSession, role_name: str) -> Role:
    """Fetch a role by name, creating it if it doesn't exist."""
    result = await db.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        await db.flush()
    return role


async def register_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    password: str,
    phone: Optional[str] = None,
    role_name: str = "student",
) -> User:
    """Create a new user with the given role."""
    # Check uniqueness
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    role = await get_or_create_role(db, role_name)

    user = User(
        email=email,
        full_name=full_name,
        phone=phone,
        hashed_password=hash_password(password),
    )
    user.roles.append(role)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("user_registered", user_id=user.id, email=email)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """Verify credentials and return the user."""
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def create_session(
    db: AsyncSession,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> dict:
    """Issue JWT tokens and persist a session row."""
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    session = Session(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    db.add(session)
    await db.flush()
    logger.info("session_created", user_id=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def revoke_session(db: AsyncSession, user_id: int, token: str):
    """Mark a session as inactive (logout)."""
    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.token == token,
            Session.is_active == True,  # noqa: E712
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.is_active = False
        await db.flush()
        logger.info("session_revoked", user_id=user_id)
