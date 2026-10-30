from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserUpdateProfileRequest
from app.schemas.auth import LogoutResponse
from app.modules.auth.service import AuthService

router = APIRouter(tags=["Authentication & Profile"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Fetch profile and authoritative role for currently authenticated user."""
    return AuthService.get_current_profile(current_user)


@router.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    payload: UserUpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile details for currently authenticated user."""
    return AuthService.update_profile(current_user, payload, db)


@router.post("/auth/logout", response_model=LogoutResponse)
def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke application session and log audit event."""
    return AuthService.logout(current_user, db)
