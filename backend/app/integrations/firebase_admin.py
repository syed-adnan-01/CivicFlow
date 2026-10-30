import logging
from typing import Any, Dict
import firebase_admin
from firebase_admin import auth, credentials
from app.core.config import settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)

_firebase_app: firebase_admin.App | None = None


def init_firebase_admin() -> None:
    """Initialize Firebase Admin SDK once during app startup."""
    global _firebase_app
    if _firebase_app is not None or len(firebase_admin._apps) > 0:
        return

    try:
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
            _firebase_app = firebase_admin.initialize_app(
                cred,
                {"projectId": settings.FIREBASE_PROJECT_ID},
            )
        else:
            # Uses Application Default Credentials (ADC) or default project
            _firebase_app = firebase_admin.initialize_app(
                options={"projectId": settings.FIREBASE_PROJECT_ID}
            )
        logger.info("Firebase Admin SDK initialized successfully for project: %s", settings.FIREBASE_PROJECT_ID)
    except Exception as exc:
        logger.warning(
            "Firebase Admin SDK initialization deferred or warning: %s. "
            "Ensure credentials or ADC are configured.",
            exc,
        )


def verify_firebase_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token using the Firebase Admin SDK.
    Enforces expected project ID audience and revocation policy.
    Fails closed if verification fails.
    """
    if not id_token:
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Authentication token required.")

    # Allow mock tokens in development / test mode without hitting external Firebase
    if settings.APP_ENV in ("development", "test") and (
        id_token.startswith("citizen_") or id_token.startswith("mock_") or id_token.startswith("test_")
    ):
        return {
            "uid": f"user_{id_token}",
            "aud": settings.FIREBASE_PROJECT_ID,
            "phone_number": "+919999900000",
            "name": "Test User",
        }

    try:
        claims = auth.verify_id_token(
            id_token,
            check_revoked=settings.FIREBASE_CHECK_REVOKED,
        )
        # Validate audience
        aud = claims.get("aud")
        if aud != settings.FIREBASE_PROJECT_ID:
            logger.warning("Token audience mismatch. Expected: %s, got: %s", settings.FIREBASE_PROJECT_ID, aud)
            raise AppError(
                status_code=401,
                code="UNAUTHENTICATED",
                message="Invalid authentication credentials.",
            )
        return claims
    except AppError:
        raise
    except auth.RevokedIdTokenError:
        logger.warning("Firebase ID token has been revoked.")
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Authentication token has been revoked.")
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase ID token has expired.")
        raise AppError(status_code=401, code="UNAUTHENTICATED", message="Authentication token has expired.")
    except Exception as exc:
        logger.warning("Firebase token verification failure: %s", type(exc).__name__)
        raise AppError(
            status_code=401,
            code="UNAUTHENTICATED",
            message="Invalid or expired authentication credentials.",
        )
