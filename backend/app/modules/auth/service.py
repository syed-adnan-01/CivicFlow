from sqlalchemy.orm import Session
from app.core.time import utc_now
from app.models.user import User
from app.models.audit_event import AuditEvent
from app.schemas.user import UserProfileResponse, UserUpdateProfileRequest
from app.schemas.auth import LogoutResponse


class AuthService:
    @staticmethod
    def get_current_profile(user: User) -> UserProfileResponse:
        return UserProfileResponse.model_validate(user)

    @staticmethod
    def update_profile(user: User, payload: UserUpdateProfileRequest, db: Session) -> UserProfileResponse:
        if payload.display_name is not None:
            user.display_name = payload.display_name
        db.commit()
        db.refresh(user)
        return UserProfileResponse.model_validate(user)

    @staticmethod
    def logout(user: User, db: Session) -> LogoutResponse:
        audit = AuditEvent(
            actor_id=user.id,
            actor_role=user.role,
            office_id=user.office_id,
            action="USER_LOGOUT",
            resource_type="USER",
            resource_id=str(user.id),
            timestamp=utc_now(),
            reason="User initiated session logout",
        )
        db.add(audit)
        db.commit()
        return LogoutResponse(message="Successfully logged out.", status="ok")
