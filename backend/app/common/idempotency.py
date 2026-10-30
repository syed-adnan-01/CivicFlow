import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.core.time import utc_now, ensure_utc
from app.models.idempotency_key import IdempotencyKey


def compute_request_hash(method: str, path: str, actor_id: uuid.UUID, body: Any) -> str:
    """Create canonical fingerprint of HTTP method, route, actor and request body."""
    body_str = json.dumps(body, sort_keys=True, default=str) if body else ""
    raw = f"{method.upper()}:{path}:{actor_id}:{body_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_key(key: str) -> str:
    """Hash the client-supplied Idempotency-Key header."""
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()


class IdempotencyService:
    @staticmethod
    def check_idempotency(
        db: Session,
        actor_id: uuid.UUID,
        scope: str,
        idempotency_key: str,
        request_hash: str,
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        """
        Check if request was already processed.
        - If same key & same payload -> return stored (status, body)
        - If same key & different payload -> raise 409 IDEMPOTENCY_KEY_REUSED
        - If not found -> return None
        """
        key_h = hash_key(idempotency_key)
        record = (
            db.query(IdempotencyKey)
            .filter_by(actor_id=actor_id, scope=scope, key_hash=key_h)
            .first()
        )
        if not record:
            return None

        # Check if expired
        if ensure_utc(record.expires_at) < utc_now():
            return None

        if record.request_hash != request_hash:
            raise AppError(
                status_code=409,
                code="IDEMPOTENCY_KEY_REUSED",
                message="This idempotency key was previously used with a different request payload.",
            )

        if record.response_status is not None and record.response_body is not None:
            return record.response_status, json.loads(record.response_body)

        return None

    @staticmethod
    def save_idempotency(
        db: Session,
        actor_id: uuid.UUID,
        scope: str,
        idempotency_key: str,
        request_hash: str,
        response_status: int,
        response_body: Dict[str, Any],
    ) -> None:
        """Store the response for idempotent replay."""
        key_h = hash_key(idempotency_key)
        expires_at = utc_now() + timedelta(hours=settings.IDEMPOTENCY_RETENTION_HOURS)

        record = (
            db.query(IdempotencyKey)
            .filter_by(actor_id=actor_id, scope=scope, key_hash=key_h)
            .first()
        )
        body_json = json.dumps(response_body, default=str)
        if record:
            record.response_status = response_status
            record.response_body = body_json
            record.expires_at = expires_at
        else:
            record = IdempotencyKey(
                id=uuid.uuid4(),
                actor_id=actor_id,
                scope=scope,
                key_hash=key_h,
                request_hash=request_hash,
                response_status=response_status,
                response_body=body_json,
                expires_at=expires_at,
            )
            db.add(record)
