import uuid
from datetime import datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.core.time import utc_now, ensure_utc
from app.models.appointment import Appointment
from app.models.checkin_reference import CheckinReference
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.modules.qr_references.crypto import generate_secure_qr_reference, hash_qr_reference


class QRReferenceService:
    @staticmethod
    def create_initial_reference(
        db: Session,
        appointment_id: uuid.UUID,
        expires_at: datetime,
        created_by_user_id: Optional[uuid.UUID] = None,
    ) -> str:
        """
        Generate raw reference, persist its SHA-256 hash, and return the raw reference once.
        The raw reference is never stored or logged.
        """
        raw_ref = generate_secure_qr_reference()
        ref_hash = hash_qr_reference(raw_ref)

        record = CheckinReference(
            id=uuid.uuid4(),
            appointment_id=appointment_id,
            reference_hash=ref_hash,
            expires_at=expires_at,
            created_by_user_id=created_by_user_id,
        )
        db.add(record)
        return raw_ref

    @staticmethod
    def rotate_reference(
        db: Session,
        appointment_id: uuid.UUID,
        user: User,
    ) -> str:
        """
        Rotates QR reference for an active BOOKED appointment.
        Invalidates old unused references and issues a new raw reference.
        """
        # 1. Lock appointment row
        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .with_for_update()
            .first()
        )
        if not appointment:
            raise AppError(status_code=404, code="APPOINTMENT_NOT_FOUND", message="Appointment not found.")

        # 2. Check ownership
        if user.role == "CITIZEN" and appointment.citizen_id != user.id:
            raise AppError(status_code=404, code="APPOINTMENT_NOT_FOUND", message="Appointment not found.")

        # 3. Check appointment status
        if appointment.status != "BOOKED":
            raise AppError(
                status_code=409,
                code="QR_NOT_ROTATABLE",
                message=f"Cannot rotate QR reference for appointment in '{appointment.status}' state.",
            )

        # 4. Check that check-in window has not expired
        now = utc_now()
        if now > ensure_utc(appointment.check_in_close_at):
            raise AppError(
                status_code=409,
                code="QR_NOT_ROTATABLE",
                message="Check-in window has closed. QR cannot be rotated.",
            )

        # 5. Rate limit: prototype limit (e.g. 3 rotations per 10 minutes)
        window_start = now - timedelta(seconds=settings.QR_ROTATION_WINDOW_SECONDS)
        recent_rotations_count = (
            db.query(CheckinReference)
            .filter(
                CheckinReference.appointment_id == appointment.id,
                CheckinReference.created_at >= window_start,
            )
            .count()
        )
        if recent_rotations_count >= settings.QR_ROTATION_LIMIT:
            raise AppError(
                status_code=429,
                code="RATE_LIMITED",
                message=f"QR rotation limit reached ({settings.QR_ROTATION_LIMIT} rotations per {settings.QR_ROTATION_WINDOW_SECONDS // 60} minutes). Please wait before rotating again.",
            )

        # 6. Invalidate existing unused references
        unused_refs = (
            db.query(CheckinReference)
            .filter(
                CheckinReference.appointment_id == appointment.id,
                CheckinReference.invalidated_at.is_(None),
                CheckinReference.used_at.is_(None),
            )
            .all()
        )
        for ref in unused_refs:
            ref.invalidated_at = now
            ref.invalidation_reason = "ROTATED"

        # 7. Generate new raw reference and store hash
        raw_ref = generate_secure_qr_reference()
        ref_hash = hash_qr_reference(raw_ref)

        new_ref_record = CheckinReference(
            id=uuid.uuid4(),
            appointment_id=appointment.id,
            reference_hash=ref_hash,
            expires_at=appointment.check_in_close_at,
            created_by_user_id=user.id,
        )
        db.add(new_ref_record)

        # 8. Update appointment metadata & audit
        appointment.qr_rotated_at = now

        audit = AuditEvent(
            actor_id=user.id,
            actor_role=user.role,
            office_id=appointment.office_id,
            action="QR_ROTATED",
            resource_type="APPOINTMENT",
            resource_id=str(appointment.id),
            timestamp=now,
            reason="User requested QR reference rotation",
        )
        db.add(audit)

        db.commit()
        return raw_ref

    @staticmethod
    def resolve_and_lock_reference(
        db: Session,
        raw_reference: str,
    ) -> Tuple[CheckinReference, Appointment]:
        """
        Shared contract for Member 2:
        Resolves raw reference, verifies validity and locks record.
        """
        ref_hash = hash_qr_reference(raw_reference.strip())
        record = (
            db.query(CheckinReference)
            .filter(CheckinReference.reference_hash == ref_hash)
            .with_for_update()
            .first()
        )
        if not record:
            raise AppError(status_code=404, code="NOT_FOUND", message="Invalid QR reference.")

        if record.used_at is not None:
            raise AppError(status_code=409, code="CONFLICT", message="QR reference has already been used.")

        if record.invalidated_at is not None:
            raise AppError(
                status_code=409,
                code="CONFLICT",
                message=f"QR reference is no longer valid (reason: {record.invalidation_reason}).",
            )

        now = utc_now()
        if now > ensure_utc(record.expires_at):
            raise AppError(status_code=409, code="CONFLICT", message="QR reference has expired.")

        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == record.appointment_id)
            .with_for_update()
            .first()
        )
        if not appointment:
            raise AppError(status_code=404, code="APPOINTMENT_NOT_FOUND", message="Associated appointment not found.")

        return record, appointment

    @staticmethod
    def mark_reference_used(db: Session, record: CheckinReference) -> None:
        """Mark reference as used inside caller's transaction."""
        record.used_at = utc_now()
