import uuid
from datetime import date, timedelta
from unittest.mock import patch
import pytest

from app.core.time import utc_now
from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.checkin_reference import CheckinReference
from app.models.user import User


@pytest.fixture
def test_data(db_session):
    office_id = uuid.uuid4()
    service_id = uuid.uuid4()

    office = Office(id=office_id, name="Urban Office", timezone="Asia/Kolkata", is_active=True)
    service = Service(id=service_id, office_id=office_id, name="Certificate Service", average_service_duration_minutes=15, is_active=True)
    policy = QueuePolicy(office_id=office_id, service_id=service_id, slot_duration_minutes=15, walk_in_share=0.20, checkin_open_minutes=15, checkin_close_minutes=10)

    now = utc_now()
    slot_id = uuid.uuid4()
    slot = AppointmentSlot(
        id=slot_id,
        office_id=office_id,
        service_id=service_id,
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=2, minutes=15),
        operating_date=date(2026, 11, 5),
        block_start_at=now + timedelta(hours=2),
        capacity=2,
        booked_count=0,
        status="OPEN",
        capacity_policy_version=1,
    )

    resched_slot_id = uuid.uuid4()
    resched_slot = AppointmentSlot(
        id=resched_slot_id,
        office_id=office_id,
        service_id=service_id,
        starts_at=now + timedelta(hours=3),
        ends_at=now + timedelta(hours=3, minutes=15),
        operating_date=date(2026, 11, 5),
        block_start_at=now + timedelta(hours=3),
        capacity=1,
        booked_count=0,
        status="OPEN",
        capacity_policy_version=1,
    )

    citizen1 = User(id=uuid.uuid4(), firebase_uid="citizen-1-uid", phone_number="+919000000001", role="CITIZEN", is_active=True)
    citizen2 = User(id=uuid.uuid4(), firebase_uid="citizen-2-uid", phone_number="+919000000002", role="CITIZEN", is_active=True)

    db_session.add_all([office, service, policy, slot, resched_slot, citizen1, citizen2])
    db_session.commit()

    return {
        "office_id": office_id,
        "service_id": service_id,
        "slot_id": slot_id,
        "resched_slot_id": resched_slot_id,
        "citizen1": citizen1,
        "citizen2": citizen2,
    }


def test_book_appointment_success(client, db_session, test_data):
    """BOOK-01: Citizen books open slot -> Appointment created, booked_count incremented, QR returned once."""
    claims = {"uid": "citizen-1-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer mock-token"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}
        res = client.post("/appointments", json=payload, headers=headers)
        assert res.status_code == 201
        res_data = res.json()
        assert "appointment" in res_data
        assert "qr_reference" in res_data
        assert res.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"

        # Check DB: booked_count incremented to 1
        slot = db_session.query(AppointmentSlot).filter_by(id=test_data["slot_id"]).first()
        assert slot.booked_count == 1
        assert slot.status == "OPEN"

        # Raw QR reference must NOT be in DB
        raw_qr = res_data["qr_reference"]
        ref_record = db_session.query(CheckinReference).first()
        assert ref_record.reference_hash != raw_qr
        assert len(ref_record.reference_hash) == 64


def test_book_duplicate_active_reservation_rejected(client, db_session, test_data):
    """BOOK-06: Citizen cannot book duplicate active appointment for same slot/service."""
    claims = {"uid": "citizen-1-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer mock-token"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}

        # First booking succeeds
        res1 = client.post("/appointments", json=payload, headers=headers)
        assert res1.status_code == 201

        # Second booking fails
        res2 = client.post("/appointments", json=payload, headers=headers)
        assert res2.status_code == 409
        assert res2.json()["error"]["code"] == "DUPLICATE_ACTIVE_APPOINTMENT"


def test_book_appointment_idempotency(client, db_session, test_data):
    """BOOK-04 & BOOK-05: Idempotency-Key behavior."""
    claims = {"uid": "citizen-1-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer mock-token", "Idempotency-Key": "unique-idem-key-1"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}

        # First attempt
        res1 = client.post("/appointments", json=payload, headers=headers)
        assert res1.status_code == 201
        app_id_1 = res1.json()["appointment"]["id"]

        # Replay with same key and same payload (BOOK-04)
        res2 = client.post("/appointments", json=payload, headers=headers)
        assert res2.status_code == 201
        assert res2.json()["appointment"]["id"] == app_id_1

        # Replay with same key but different payload (BOOK-05) -> 409
        diff_payload = {"slot_id": str(test_data["resched_slot_id"]), "service_id": str(test_data["service_id"])}
        res3 = client.post("/appointments", json=diff_payload, headers=headers)
        assert res3.status_code == 409
        assert res3.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_appointment_ownership_isolation(client, db_session, test_data):
    """AUTHZ-01 & AUTHZ-02: Citizens cannot view or access each other's appointments."""
    claims_1 = {"uid": "citizen-1-uid", "aud": "queueless-dev"}
    claims_2 = {"uid": "citizen-2-uid", "aud": "queueless-dev"}

    # Citizen 1 books
    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims_1):
        headers_1 = {"Authorization": "Bearer mock-token-1"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}
        res = client.post("/appointments", json=payload, headers=headers_1)
        assert res.status_code == 201
        app_id = res.json()["appointment"]["id"]

        # Citizen 1 can view own appointment
        res_view_1 = client.get(f"/appointments/{app_id}", headers=headers_1)
        assert res_view_1.status_code == 200

    # Citizen 2 tries to view Citizen 1's appointment -> 404
    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims_2):
        headers_2 = {"Authorization": "Bearer mock-token-2"}
        res_view_2 = client.get(f"/appointments/{app_id}", headers=headers_2)
        assert res_view_2.status_code == 404
        assert res_view_2.json()["error"]["code"] == "APPOINTMENT_NOT_FOUND"

        # Citizen 2 cannot cancel Citizen 1's appointment
        res_cancel = client.post(f"/appointments/{app_id}/cancel", headers=headers_2)
        assert res_cancel.status_code == 404


def test_cancel_appointment_releases_capacity(client, db_session, test_data):
    """BOOK-08: Cancel eligible booking -> Appointment marked CANCELLED, slot count decremented."""
    claims = {"uid": "citizen-1-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer mock-token"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}

        # Book
        book_res = client.post("/appointments", json=payload, headers=headers)
        app_id = book_res.json()["appointment"]["id"]

        # Cancel
        cancel_res = client.post(f"/appointments/{app_id}/cancel", json={"reason": "Cannot attend"}, headers=headers)
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

        # Check slot count is decremented to 0
        slot = db_session.query(AppointmentSlot).filter_by(id=test_data["slot_id"]).first()
        assert slot.booked_count == 0

        # Check QR reference was invalidated
        ref = db_session.query(CheckinReference).filter_by(appointment_id=uuid.UUID(app_id)).first()
        assert ref.invalidated_at is not None
        assert ref.invalidation_reason == "CANCELLED"


def test_reschedule_appointment(client, db_session, test_data):
    """BOOK-11 & BOOK-14: Rescheduling reserves new slot, decrements old slot, invalidates old QR."""
    claims = {"uid": "citizen-1-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer mock-token"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}

        # Book old slot
        res_book = client.post("/appointments", json=payload, headers=headers)
        old_app_id = res_book.json()["appointment"]["id"]

        # Reschedule to new slot
        resched_payload = {"new_slot_id": str(test_data["resched_slot_id"])}
        res_resched = client.post(f"/appointments/{old_app_id}/reschedule", json=resched_payload, headers=headers)
        assert res_resched.status_code == 200
        new_app_data = res_resched.json()
        new_app_id = new_app_data["appointment"]["id"]
        assert new_app_data["appointment"]["rescheduled_from_id"] == old_app_id

        # Verify old appointment is marked RESCHEDULED
        old_app = db_session.query(Appointment).filter_by(id=uuid.UUID(old_app_id)).first()
        assert old_app.status == "RESCHEDULED"
        assert str(old_app.rescheduled_to_id) == new_app_id

        # Verify slot counts: old slot count is 0, new slot count is 1
        old_slot = db_session.query(AppointmentSlot).filter_by(id=test_data["slot_id"]).first()
        new_slot = db_session.query(AppointmentSlot).filter_by(id=test_data["resched_slot_id"]).first()
        assert old_slot.booked_count == 0
        assert new_slot.booked_count == 1

        # Verify old QR reference is invalidated with reason RESCHEDULED
        old_ref = db_session.query(CheckinReference).filter_by(appointment_id=uuid.UUID(old_app_id)).first()
        assert old_ref.invalidation_reason == "RESCHEDULED"


def test_qr_rotation(client, db_session, test_data):
    """QR-04 & QR-05: Authenticated QR rotation issues fresh raw reference and invalidates old."""
    claims = {"uid": "citizen-1-uid", "aud": "queueless-dev"}

    with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
        headers = {"Authorization": "Bearer mock-token"}
        payload = {"slot_id": str(test_data["slot_id"]), "service_id": str(test_data["service_id"])}

        # Book
        book_res = client.post("/appointments", json=payload, headers=headers)
        app_id = book_res.json()["appointment"]["id"]
        first_raw_qr = book_res.json()["qr_reference"]

        # Rotate QR
        rot_res = client.post(f"/appointments/{app_id}/qr/rotate", headers=headers)
        assert rot_res.status_code == 200
        rot_data = rot_res.json()
        second_raw_qr = rot_data["qr_reference"]
        assert second_raw_qr != first_raw_qr
        assert rot_res.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"

        # Verify in DB: first reference is ROTATED, second reference is active
        refs = db_session.query(CheckinReference).filter_by(appointment_id=uuid.UUID(app_id)).order_by(CheckinReference.created_at).all()
        assert len(refs) == 2
        assert refs[0].invalidated_at is not None
        assert refs[0].invalidation_reason == "ROTATED"
        assert refs[1].invalidated_at is None
        assert refs[1].used_at is None
