import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import utc_now, ensure_utc
from app.models.user import User
from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.checkin_reference import CheckinReference
from app.models.audit_event import AuditEvent
from app.common.permissions import verify_appointment_access
from app.common.idempotency import IdempotencyService, compute_request_hash
from app.modules.qr_references.service import QRReferenceService
from app.schemas.appointment import (
    BookAppointmentRequest,
    BookAppointmentResponse,
    AppointmentDetailResponse,
    CancelAppointmentRequest,
    RescheduleAppointmentRequest,
    RotateQRResponse,
)


class AppointmentService:
    @staticmethod
    def book_appointment(
        db: Session,
        user: User,
        payload: BookAppointmentRequest,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[BookAppointmentResponse, bool]:
        """
        Transactional appointment booking:
        - Locks slot row with FOR UPDATE
        - Enforces slot capacity and state
        - Prevents duplicate active reservations
        - Generates 256-bit QR reference and persists only its hash
        - Atomically increments booked_count and logs audit event
        - Supports Idempotency-Key
        """
        req_hash = ""
        if idempotency_key:
            req_hash = compute_request_hash("POST", "/appointments", user.id, payload.model_dump())
            cached = IdempotencyService.check_idempotency(
                db, user.id, "appointment.book", idempotency_key, req_hash
            )
            if cached:
                cached_status, cached_body = cached
                return BookAppointmentResponse(**cached_body), True

        now = utc_now()

        # 1. Lock slot row
        slot = (
            db.query(AppointmentSlot)
            .filter(AppointmentSlot.id == payload.slot_id)
            .with_for_update()
            .first()
        )
        if not slot:
            raise AppError(status_code=404, code="SLOT_NOT_FOUND", message="Requested appointment slot not found.")

        # 2. Confirm slot belongs to the selected service
        if slot.service_id != payload.service_id:
            raise AppError(status_code=400, code="VALIDATION_ERROR", message="Slot does not belong to specified service.")

        # 3. Confirm slot is OPEN, in the future and has capacity
        if slot.status == "CLOSED":
            raise AppError(status_code=409, code="SLOT_FULL", message="This appointment slot is closed.")

        if slot.booked_count >= slot.capacity:
            raise AppError(status_code=409, code="SLOT_FULL", message="This appointment slot is no longer available.")

        if ensure_utc(slot.starts_at) <= now:
            raise AppError(status_code=400, code="VALIDATION_ERROR", message="Cannot book a slot in the past.")

        # 4. Check duplicate active reservation for this citizen, service, and slot
        existing_active = (
            db.query(Appointment)
            .filter(
                Appointment.citizen_id == user.id,
                Appointment.office_id == slot.office_id,
                Appointment.service_id == slot.service_id,
                Appointment.slot_id == slot.id,
                Appointment.status == "BOOKED",
            )
            .first()
        )
        if existing_active:
            raise AppError(
                status_code=409,
                code="DUPLICATE_ACTIVE_APPOINTMENT",
                message="You already have an active booking for this service and slot.",
            )

        # 5. Load effective policy for check-in window
        policy = (
            db.query(QueuePolicy)
            .filter(
                QueuePolicy.office_id == slot.office_id,
                QueuePolicy.service_id.in_([slot.service_id, None]),
            )
            .order_by(QueuePolicy.service_id.desc(), QueuePolicy.policy_version.desc())
            .first()
        )
        checkin_open_min = policy.checkin_open_minutes if policy else 15
        checkin_close_min = policy.checkin_close_minutes if policy else 10

        check_in_open_at = ensure_utc(slot.starts_at) - timedelta(minutes=checkin_open_min)
        check_in_close_at = ensure_utc(slot.starts_at) + timedelta(minutes=checkin_close_min)

        booking_ref = f"QL-{uuid.uuid4().hex[:8].upper()}"

        # 6. Insert appointment
        appointment = Appointment(
            id=uuid.uuid4(),
            citizen_id=user.id,
            office_id=slot.office_id,
            service_id=slot.service_id,
            slot_id=slot.id,
            status="BOOKED",
            booking_reference=booking_ref,
            slot_start_at=slot.starts_at,
            check_in_open_at=check_in_open_at,
            check_in_close_at=check_in_close_at,
            created_at=now,
            updated_at=now,
        )
        db.add(appointment)
        db.flush()

        # 7. Generate initial QR reference (raw returned once, hash stored)
        raw_qr = QRReferenceService.create_initial_reference(
            db=db,
            appointment_id=appointment.id,
            expires_at=check_in_close_at,
            created_by_user_id=user.id,
        )

        # 8. Increment booked_count
        slot.booked_count += 1
        if slot.booked_count >= slot.capacity:
            slot.status = "FULL"

        # 9. Audit event
        audit = AuditEvent(
            actor_id=user.id,
            actor_role=user.role,
            office_id=slot.office_id,
            action="APPOINTMENT_BOOKED",
            resource_type="APPOINTMENT",
            resource_id=str(appointment.id),
            timestamp=now,
            reason="Citizen booked appointment",
        )
        db.add(audit)

        # 10. Build response and record idempotency
        response_data = BookAppointmentResponse(
            appointment=AppointmentDetailResponse.model_validate(appointment),
            qr_reference=raw_qr,
        )

        if idempotency_key:
            IdempotencyService.save_idempotency(
                db,
                user.id,
                "appointment.book",
                idempotency_key,
                req_hash,
                201,
                response_data.model_dump(),
            )

        db.commit()
        return response_data, False

    @staticmethod
    def list_my_appointments(db: Session, user: User) -> List[AppointmentDetailResponse]:
        """Citizens can list ONLY their own appointments."""
        records = (
            db.query(Appointment)
            .filter(Appointment.citizen_id == user.id)
            .order_by(Appointment.created_at.desc())
            .all()
        )
        return [AppointmentDetailResponse.model_validate(a) for a in records]

    @staticmethod
    def get_appointment_detail(
        db: Session,
        appointment_id: uuid.UUID,
        user: User,
    ) -> AppointmentDetailResponse:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise AppError(status_code=404, code="APPOINTMENT_NOT_FOUND", message="Appointment not found.")

        verify_appointment_access(user, appointment)
        return AppointmentDetailResponse.model_validate(appointment)

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: uuid.UUID,
        user: User,
        payload: CancelAppointmentRequest,
    ) -> AppointmentDetailResponse:
        """
        Transactional cancellation:
        - Locks appointment and slot row
        - Decrements slot booked_count
        - Reopens slot only if not administratively closed
        - Invalidates unused QR references
        """
        now = utc_now()

        # 1. Lock appointment row
        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .with_for_update()
            .first()
        )
        if not appointment:
            raise AppError(status_code=404, code="APPOINTMENT_NOT_FOUND", message="Appointment not found.")

        verify_appointment_access(user, appointment)

        if appointment.status != "BOOKED":
            raise AppError(
                status_code=409,
                code="APPOINTMENT_NOT_CANCELLABLE",
                message=f"Appointment in '{appointment.status}' state cannot be cancelled.",
            )

        # 2. Lock associated slot row
        slot = (
            db.query(AppointmentSlot)
            .filter(AppointmentSlot.id == appointment.slot_id)
            .with_for_update()
            .first()
        )

        # 3. Update appointment
        appointment.status = "CANCELLED"
        appointment.cancelled_at = now
        appointment.cancellation_reason = payload.reason

        # 4. Release slot capacity
        if slot:
            slot.booked_count = max(0, slot.booked_count - 1)
            # Reopen slot if under capacity and slot was FULL (preserve CLOSED status if administrative/out-of-hours)
            if slot.booked_count < slot.capacity and slot.status == "FULL":
                slot.status = "OPEN"

        # 5. Invalidate all unused QR references
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
            ref.invalidation_reason = "CANCELLED"

        # 6. Audit
        audit = AuditEvent(
            actor_id=user.id,
            actor_role=user.role,
            office_id=appointment.office_id,
            action="APPOINTMENT_CANCELLED",
            resource_type="APPOINTMENT",
            resource_id=str(appointment.id),
            timestamp=now,
            reason=payload.reason,
        )
        db.add(audit)

        db.commit()
        db.refresh(appointment)
        return AppointmentDetailResponse.model_validate(appointment)

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: uuid.UUID,
        user: User,
        payload: RescheduleAppointmentRequest,
    ) -> BookAppointmentResponse:
        """
        Transactional rescheduling:
        - Locks old appointment row
        - Locks old and new slot rows in deterministic order to prevent deadlocks
        - Decrements old slot, reserves new slot
        - Preserves history via rescheduled_from_id / rescheduled_to_id
        - Invalidates old QR and generates new QR reference
        """
        now = utc_now()

        # 1. Lock old appointment
        old_appointment = (
            db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .with_for_update()
            .first()
        )
        if not old_appointment:
            raise AppError(status_code=404, code="APPOINTMENT_NOT_FOUND", message="Appointment not found.")

        verify_appointment_access(user, old_appointment)

        if old_appointment.status != "BOOKED":
            raise AppError(
                status_code=409,
                code="APPOINTMENT_NOT_RESCHEDULABLE",
                message=f"Appointment in '{old_appointment.status}' state cannot be rescheduled.",
            )

        if old_appointment.slot_id == payload.new_slot_id:
            raise AppError(status_code=400, code="VALIDATION_ERROR", message="Cannot reschedule to the exact same slot.")

        # 2. Deterministic slot lock order by slot UUID to prevent deadlocks
        slot_ids = sorted([old_appointment.slot_id, payload.new_slot_id], key=lambda u: u.bytes)
        locked_slots = {}
        for s_id in slot_ids:
            s = db.query(AppointmentSlot).filter(AppointmentSlot.id == s_id).with_for_update().first()
            if not s:
                raise AppError(status_code=404, code="SLOT_NOT_FOUND", message=f"Slot {s_id} not found.")
            locked_slots[s_id] = s

        old_slot = locked_slots[old_appointment.slot_id]
        new_slot = locked_slots[payload.new_slot_id]

        # 3. Verify new slot
        if new_slot.service_id != old_appointment.service_id:
            raise AppError(status_code=400, code="VALIDATION_ERROR", message="New slot does not match the original service.")

        if new_slot.status == "CLOSED" or new_slot.booked_count >= new_slot.capacity:
            raise AppError(status_code=409, code="SLOT_FULL", message="The selected new slot is no longer available.")

        if ensure_utc(new_slot.starts_at) <= now:
            raise AppError(status_code=400, code="VALIDATION_ERROR", message="Cannot reschedule to a slot in the past.")

        # 4. Check check-in window for new appointment
        policy = (
            db.query(QueuePolicy)
            .filter(
                QueuePolicy.office_id == new_slot.office_id,
                QueuePolicy.service_id.in_([new_slot.service_id, None]),
            )
            .order_by(QueuePolicy.service_id.desc(), QueuePolicy.policy_version.desc())
            .first()
        )
        checkin_open_min = policy.checkin_open_minutes if policy else 15
        checkin_close_min = policy.checkin_close_minutes if policy else 10

        new_checkin_open = ensure_utc(new_slot.starts_at) - timedelta(minutes=checkin_open_min)
        new_checkin_close = ensure_utc(new_slot.starts_at) + timedelta(minutes=checkin_close_min)

        new_booking_ref = f"QL-{uuid.uuid4().hex[:8].upper()}"

        # 5. Create new appointment
        new_appointment = Appointment(
            id=uuid.uuid4(),
            citizen_id=user.id,
            office_id=new_slot.office_id,
            service_id=new_slot.service_id,
            slot_id=new_slot.id,
            status="BOOKED",
            booking_reference=new_booking_ref,
            slot_start_at=new_slot.starts_at,
            check_in_open_at=new_checkin_open,
            check_in_close_at=new_checkin_close,
            rescheduled_from_id=old_appointment.id,
            created_at=now,
            updated_at=now,
        )
        db.add(new_appointment)
        db.flush()

        # 6. Update old appointment
        old_appointment.status = "RESCHEDULED"
        old_appointment.rescheduled_to_id = new_appointment.id

        # 7. Release old slot capacity
        old_slot.booked_count = max(0, old_slot.booked_count - 1)
        if old_slot.booked_count < old_slot.capacity and old_slot.status == "FULL":
            old_slot.status = "OPEN"

        # 8. Reserve new slot capacity
        new_slot.booked_count += 1
        if new_slot.booked_count >= new_slot.capacity:
            new_slot.status = "FULL"

        # 9. Invalidate old QR references
        old_refs = (
            db.query(CheckinReference)
            .filter(
                CheckinReference.appointment_id == old_appointment.id,
                CheckinReference.invalidated_at.is_(None),
                CheckinReference.used_at.is_(None),
            )
            .all()
        )
        for ref in old_refs:
            ref.invalidated_at = now
            ref.invalidation_reason = "RESCHEDULED"

        # 10. Issue new QR reference
        new_raw_qr = QRReferenceService.create_initial_reference(
            db=db,
            appointment_id=new_appointment.id,
            expires_at=new_checkin_close,
            created_by_user_id=user.id,
        )

        # 11. Audits
        db.add(
            AuditEvent(
                actor_id=user.id,
                actor_role=user.role,
                office_id=old_appointment.office_id,
                action="APPOINTMENT_RESCHEDULED",
                resource_type="APPOINTMENT",
                resource_id=str(old_appointment.id),
                timestamp=now,
                reason=f"Rescheduled to appointment {new_appointment.id}",
            )
        )
        db.add(
            AuditEvent(
                actor_id=user.id,
                actor_role=user.role,
                office_id=new_appointment.office_id,
                action="APPOINTMENT_BOOKED",
                resource_type="APPOINTMENT",
                resource_id=str(new_appointment.id),
                timestamp=now,
                reason=f"Rescheduled from appointment {old_appointment.id}",
            )
        )

        db.commit()
        return BookAppointmentResponse(
            appointment=AppointmentDetailResponse.model_validate(new_appointment),
            qr_reference=new_raw_qr,
        )

    @staticmethod
    def rotate_qr(
        db: Session,
        appointment_id: uuid.UUID,
        user: User,
    ) -> RotateQRResponse:
        raw_qr = QRReferenceService.rotate_reference(db, appointment_id, user)
        # Fetch appointment to get latest expires_at and rotated_at
        app = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        return RotateQRResponse(
            qr_reference=raw_qr,
            rotated_at=app.qr_rotated_at,
            expires_at=app.check_in_close_at,
        )
