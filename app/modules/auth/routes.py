"""Auth module — API routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, oauth2_scheme
from app.db.database import get_db
from app.modules.auth import schemas, services
from app.modules.auth.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.TokenResponse, status_code=201)
async def register(
    body: schemas.RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new student account and return JWT tokens."""
    user = await services.register_user(
        db,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        phone=body.phone,
    )
    tokens = await services.create_session(
        db,
        user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return schemas.TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=schemas.UserResponse.model_validate(user),
    )


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    body: schemas.LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return JWT tokens."""
    user = await services.authenticate_user(db, body.email, body.password)
    tokens = await services.create_session(
        db,
        user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return schemas.TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=schemas.UserResponse.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return schemas.UserResponse.model_validate(current_user)


@router.post("/logout", response_model=schemas.MessageResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current session."""
    await services.revoke_session(db, current_user.id, token)
    return schemas.MessageResponse(message="Logged out successfully")
