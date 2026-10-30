"""
Section 16 Concurrency Tests:
Do not validate transactional correctness only with SQLite or mocked repositories.
Use PostgreSQL for concurrency tests.
"""
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
import pytest

from app.core.config import settings
from app.core.time import utc_now
from app.models.office import Office
from app.models.service import Service
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.user import User

from tests.conftest import test_engine

is_postgresql = test_engine.dialect.name == "postgresql"

pytestmark = pytest.mark.skipif(
    not is_postgresql,
    reason="Section 16: Concurrency tests require a real PostgreSQL database to avoid SQLite threading limitations.",
)


@pytest.fixture
def concurrency_data(db_session):
    office_id = uuid.uuid4()
    service_id = uuid.uuid4()

    office = Office(id=office_id, name="Concurrency Office", is_active=True)
    service = Service(id=service_id, office_id=office_id, name="Concurrency Service", average_service_duration_minutes=15, is_active=True)

    citizen1 = User(id=uuid.uuid4(), firebase_uid="conc-citizen-1", role="CITIZEN", is_active=True)
    citizen2 = User(id=uuid.uuid4(), firebase_uid="conc-citizen-2", role="CITIZEN", is_active=True)

    now = utc_now()
    slot = AppointmentSlot(
        id=uuid.uuid4(),
        office_id=office_id,
        service_id=service_id,
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=2, minutes=15),
        operating_date=now.date(),
        block_start_at=now + timedelta(hours=2),
        capacity=1,
        booked_count=0,
        status="OPEN",
    )

    db_session.add_all([office, service, citizen1, citizen2, slot])
    db_session.commit()

    return {
        "office_id": office_id,
        "service_id": service_id,
        "slot_id": slot.id,
        "citizen1": citizen1,
        "citizen2": citizen2,
    }


def test_concurrent_booking_final_capacity(client, db_session, concurrency_data):
    """
    Section 16 Scenario 1:
    Two simultaneous requests compete for the final slot capacity of 1.
    Exactly one must succeed (201), the other must receive 409 SLOT_FULL.
    The database booked_count must equal capacity (1), never 2.
    """
    data = concurrency_data
    slot_id = str(data["slot_id"])
    service_id = str(data["service_id"])

    def make_booking(uid):
        claims = {"uid": uid, "aud": "queueless-dev"}
        with patch("app.common.dependencies.verify_firebase_id_token", return_value=claims):
            headers = {"Authorization": "Bearer mock-token"}
            payload = {"slot_id": slot_id, "service_id": service_id}
            resp = client.post("/appointments", json=payload, headers=headers)
            return resp.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(make_booking, "conc-citizen-1")
        f2 = executor.submit(make_booking, "conc-citizen-2")
        results = [f1.result(), f2.result()]

    assert sorted(results) == [201, 409]

    slot = db_session.query(AppointmentSlot).filter_by(id=data["slot_id"]).first()
    assert slot.booked_count == 1
    assert slot.status == "FULL"
