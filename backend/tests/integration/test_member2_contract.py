import uuid
from datetime import timedelta
import pytest

from app.core.time import utc_now
from app.core.errors import AppError
from app.models.office import Office
from app.models.service import Service
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.user import User
from app.modules.qr_references.service import QRReferenceService


def test_member2_checkin_resolution_success(db_session):
    """
    Test Member 2's check-in integration contract:
    - Member 1 creates appointment and QR reference.
    - Member 2 calls resolve_and_lock_reference(db, raw_reference).
    - Checks appointment status, check-in window, and marks reference used.
    """
    office_id = uuid.uuid4()
    service_id = uuid.uuid4()
    citizen_id = uuid.uuid4()
    slot_id = uuid.uuid4()
    app_id = uuid.uuid4()

    now = utc_now()
    office = Office(id=office_id, name="Check-in Office", is_active=True)
    service = Service(id=service_id, office_id=office_id, name="Check-in Service", is_active=True)
    citizen = User(id=citizen_id, firebase_uid="checkin-user", role="CITIZEN", is_active=True)
    slot = AppointmentSlot(
        id=slot_id,
        office_id=office_id,
        service_id=service_id,
        starts_at=now + timedelta(minutes=10),
        ends_at=now + timedelta(minutes=25),
        operating_date=now.date(),
        block_start_at=now,
        capacity=2,
        booked_count=1,
        status="OPEN",
    )
    appointment = Appointment(
        id=app_id,
        citizen_id=citizen_id,
        office_id=office_id,
        service_id=service_id,
        slot_id=slot_id,
        status="BOOKED",
        slot_start_at=slot.starts_at,
        check_in_open_at=now - timedelta(minutes=5),
        check_in_close_at=now + timedelta(minutes=20),
    )

    db_session.add_all([office, service, citizen, slot, appointment])
    db_session.flush()

    # Member 1 issues raw reference
    raw_ref = QRReferenceService.create_initial_reference(
        db=db_session,
        appointment_id=app_id,
        expires_at=appointment.check_in_close_at,
        created_by_user_id=citizen_id,
    )
    db_session.commit()

    # Member 2's checkin handler consumes raw reference
    ref_record, app_record = QRReferenceService.resolve_and_lock_reference(
        db=db_session,
        raw_reference=raw_ref,
    )

    assert ref_record.appointment_id == app_id
    assert app_record.id == app_id
    assert app_record.status == "BOOKED"
    assert ref_record.used_at is None

    # Member 2 marks reference used
    QRReferenceService.mark_reference_used(db_session, ref_record)
    app_record.status = "CHECKED_IN"
    db_session.commit()

    # Second scan attempt must be rejected (one-time use)
    with pytest.raises(AppError) as exc_info:
        QRReferenceService.resolve_and_lock_reference(db_session, raw_ref)
    assert exc_info.value.code == "CONFLICT"
    assert "already been used" in exc_info.value.message
