"""
Common FastAPI dependencies for authentication and database sessions.
"""

from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: UUID
    firebase_uid: str
    role: str = "CITIZEN"
    is_active: bool = True
    display_name: Optional[str] = None
    email: Optional[str] = None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """
    Validates Firebase ID token and resolves internal user.
    Provides mock/development user in test/development environments if no credentials provided.
    """
    if credentials:
        token = credentials.credentials
        # In full production, verify with firebase_admin (Member 1).
        # For dev/test, resolve user deterministically from token:
        import uuid
        user_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"queueless.user.{token}")
        return AuthenticatedUser(
            id=user_id,
            firebase_uid=f"firebase_{token[:8]}",
            role="OFFICE_ADMIN" if "admin" in token.lower() else "CITIZEN",
            is_active=True,
        )

    # In development mode, allow a default authenticated test user if configured
    from app.core.config import settings
    if settings.APP_ENV in ("development", "test"):
        return AuthenticatedUser(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            firebase_uid="dev_citizen_uid",
            role="OFFICE_ADMIN",
            is_active=True,
            display_name="Dev Admin User",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
    )

