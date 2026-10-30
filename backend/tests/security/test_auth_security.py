import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest

from app.core.time import utc_now
from app.models.office import Office
from app.models.service import Service
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.checkin_reference import CheckinReference
from app.models.user import User


@pytest.fixture
def security_test_data(db_session):
    office_id = uuid.uuid4()
    service_id = uuid.uuid4()

    office = Office(id=office_id, name="Security Test Office", is_active=True)
    service = Service(id=service_id, office_id=office_id, name="Security Test Service", average_service_duration_minutes=15, is_active=True)

    citizen_a = User(id=uuid.uuid4(), firebase_uid="citizen-a-uid", role="CITIZEN", is_active=True)
    citizen_b = User(id=uuid.uuid4(), firebase_uid="citizen-b-uid", role="CITIZEN", is_active=True)
    inactive_user = User(id=uuid.uuid4(), firebase_uid="citizen-inactive-uid", role="CITIZEN", is_active=False)

    now = utc_now()
    slot = AppointmentSlot(
        id=uuid.uuid4(),
        office_id=office_id,
        service_id=service_id,
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=2, minutes=15),
        operating_date=now.date(),
        block_start_at=now + timedelta(hours=2),
        capacity=5,
        booked_count=1,
        status="OPEN",
    )

    appointment_a = Appointment(
        id=uuid.uuid4(),
        citizen_id=citizen_a.id,
        office_id=office_id,
        service_id=service_id,
        slot_id=slot.id,
        status="BOOKED",
        slot_start_at=slot.starts_at,
        check_in_open_at=now,
        check_in_close_at=now + timedelta(hours=2),
        created_at=now,
        updated_at=now,
    )

    db_session.add_all([office, service, citizen_a, citizen_b, inactive_user, slot, appointment_a])
    db_session.commit()

    return {
        "office_id": office_id,
        "service_id": service_id,
        "slot_id": slot.id,
        "citizen_a": citizen_a,
        "citizen_b": citizen_b,
        "inactive_user": inactive_user,
        "appointment_a": appointment_a,
    }


def test_sec_01_unauthenticated_requests_blocked(client, security_test_data):
    """Missing Authorization header must always be blocked."""
    data = security_test_data
    app_id = data["appointment_a"].id

    assert client.get("/me").status_code == 401
    assert client.get("/appointments").status_code == 401
    assert client.get(f"/appointments/{app_id}").status_code == 401
    assert client.post(f"/appointments/{app_id}/cancel").status_code == 401
    assert client.post(f"/appointments/{app_id}/qr/rotate").status_code == 401


def test_sec_02_inactive_user_cannot_access_apis(client, security_test_data):
    """Deactivated QueueLess user is denied even with valid Firebase credentials."""
    claims = {"uid": "citizen-inactive-uid", "aud": "queueless-dev"}
    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer token"}
        res = client.get("/me", headers=headers)
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "FORBIDDEN"


def test_sec_03_citizen_cannot_read_or_modify_other_citizens_appointment(client, security_test_data):
    """Citizen B cannot read, cancel, or rotate QR for Citizen A's appointment."""
    data = security_test_data
    app_id = data["appointment_a"].id
    claims_b = {"uid": "citizen-b-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims_b):
        headers = {"Authorization": "Bearer token"}

        # Attempt to read Citizen A's appointment -> 404 (does not leak existence)
        res_read = client.get(f"/appointments/{app_id}", headers=headers)
        assert res_read.status_code == 404
        assert res_read.json()["error"]["code"] == "APPOINTMENT_NOT_FOUND"

        # Attempt to cancel Citizen A's appointment -> 404
        res_cancel = client.post(f"/appointments/{app_id}/cancel", headers=headers)
        assert res_cancel.status_code == 404

        # Attempt to rotate QR for Citizen A's appointment -> 404
        res_rotate = client.post(f"/appointments/{app_id}/qr/rotate", headers=headers)
        assert res_rotate.status_code == 404


def test_sec_04_raw_qr_not_stored_in_db(client, db_session, security_test_data):
    """Confirm raw QR reference is never stored in checkin_references table."""
    data = security_test_data
    claims = {"uid": "citizen-a-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer token"}
        app_id = data["appointment_a"].id

        rot_res = client.post(f"/appointments/{app_id}/qr/rotate", headers=headers)
        assert rot_res.status_code == 200
        raw_qr = rot_res.json()["qr_reference"]

        # Search database for raw string
        all_refs = db_session.query(CheckinReference).all()
        for ref in all_refs:
            assert ref.reference_hash != raw_qr
            # Must be a 64-character SHA-256 hash
            assert len(ref.reference_hash) == 64
