import uuid
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.time import utc_now
from app.integrations.firebase_admin import verify_firebase_id_token
from app.models.user import User
from app.models.audit_event import AuditEvent

# Alias for backward-compatibility with Member 4 modules
AuthenticatedUser = User

bearer_scheme = HTTPBearer(auto_error=False)


def get_verified_firebase_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Extract and verify Firebase Bearer ID token from request."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            status_code=401,
            code="UNAUTHENTICATED",
            message="Bearer token required.",
        )
    return verify_firebase_id_token(credentials.credentials)


def get_current_user(
    claims: Dict[str, Any] = Depends(get_verified_firebase_claims),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve internal QueueLess user from verified Firebase claims.
    If user does not exist, provision as CITIZEN transactionally.
    Rejects inactive users.
    """
    firebase_uid = claims.get("uid")
    if not firebase_uid:
        raise AppError(
            status_code=401,
            code="UNAUTHENTICATED",
            message="Invalid authentication credentials; missing uid claim.",
        )

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        # First-time citizen provisioning with least-privilege CITIZEN role
        phone_number = claims.get("phone_number")
        display_name = claims.get("name") or (f"Citizen {phone_number[-4:]}" if phone_number else "Citizen")
        user = User(
            id=uuid.uuid4(),
            firebase_uid=firebase_uid,
            phone_number=phone_number,
            display_name=display_name,
            role="CITIZEN",
            is_active=True,
            last_login_at=utc_now(),
        )
        db.add(user)

        # Audit user provisioning
        audit = AuditEvent(
            actor_id=user.id,
            actor_role="CITIZEN",
            action="USER_PROVISIONED",
            resource_type="USER",
            resource_id=str(user.id),
            timestamp=utc_now(),
            reason="First-time sign-in through Firebase Authentication",
        )
        db.add(audit)
        db.commit()
        db.refresh(user)
    else:
        # Check active status
        if not user.is_active:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message="Account has been deactivated. Contact administration.",
            )
        # Update last login timestamp
        user.last_login_at = utc_now()
        db.commit()
        db.refresh(user)

    return user


def require_role(*roles: str):
    """Dependency factory ensuring current user possesses one of the allowed roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message=f"Access denied. Requires one of roles: {', '.join(roles)}",
            )
        return current_user

    return role_checker


def require_office_scope(office_id: uuid.UUID, current_user: User = Depends(get_current_user)) -> None:
    """Verifies that staff/officer has scope for the requested office."""
    if current_user.role in ("PLATFORM_ADMIN",):
        return
    if current_user.role in ("OFFICER", "OFFICE_ADMIN"):
        if current_user.office_id != office_id:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message="Access denied to this office resource.",
            )
        return
    raise AppError(
        status_code=403,
        code="FORBIDDEN",
        message="Staff office scope required.",
    )
