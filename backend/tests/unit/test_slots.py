import uuid
from datetime import date
import pytest

from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.appointment_slot import AppointmentSlot
from app.modules.appointments.slot_generator import SlotGenerator
from app.schemas.catalogue import GenerateSlotsRequest
from app.core.errors import AppError


def test_cap_01_two_counters_ten_minute_service():
    """
    CAP-01: Two active counters, 10-minute service duration, 20% walk-in reserve.
    Block capacity = 2 * (60/10) = 12
    Reserve = floor(12 * 0.20) = 2
    Appointment capacity = 10
    Slots in block (10-min slots) = 6
    Capacities: 2, 2, 2, 2, 1, 1
    """
    capacities = SlotGenerator.calculate_block_capacities(
        active_counters=2,
        service_duration_minutes=10,
        slot_duration_minutes=10,
        walk_in_share=0.20,
    )
    assert capacities == [2, 2, 2, 2, 1, 1]


def test_cap_02_one_counter_ten_minute_service():
    """
    CAP-02: One active counter, 10-minute service duration, 20% reserve.
    Block capacity = 1 * 6 = 6
    Reserve = floor(6 * 0.20) = 1
    Appointment capacity = 5
    Slots in block = 6
    Capacities: 1, 1, 1, 1, 1, 0; the 0-capacity slot must be CLOSED.
    """
    capacities = SlotGenerator.calculate_block_capacities(
        active_counters=1,
        service_duration_minutes=10,
        slot_duration_minutes=10,
        walk_in_share=0.20,
    )
    assert capacities == [1, 1, 1, 1, 1, 0]


def test_cap_03_generate_same_block_twice_idempotency(db_session):
    """CAP-03: Running slot generation twice does not create duplicate slots or drift capacity."""
    office_id = uuid.uuid4()
    service_id = uuid.uuid4()

    office = Office(id=office_id, name="Test Office", timezone="Asia/Kolkata", is_active=True)
    service = Service(
        id=service_id,
        office_id=office_id,
        name="Test Service",
        average_service_duration_minutes=15,
        is_active=True,
    )
    policy = QueuePolicy(
        office_id=office_id,
        service_id=service_id,
        slot_duration_minutes=15,
        walk_in_share=0.20,
        policy_version=1,
    )
    db_session.add_all([office, service, policy])
    db_session.commit()

    req = GenerateSlotsRequest(
        operating_date=date(2026, 11, 1),
        active_counters=2,
        start_hour=9,
        end_hour=11,  # 2 operating hours
        break_start_hour=None,
        break_end_hour=None,
    )

    # First run
    res1 = SlotGenerator.generate_slots_for_date(db_session, office_id, service_id, req)
    slot_count_1 = db_session.query(AppointmentSlot).count()
    assert slot_count_1 == 8  # 2 hours * 4 slots/hour

    # Second run without regenerate flag (idempotent skip)
    res2 = SlotGenerator.generate_slots_for_date(db_session, office_id, service_id, req)
    slot_count_2 = db_session.query(AppointmentSlot).count()
    assert slot_count_2 == slot_count_1


def test_cap_05_cannot_reduce_capacity_below_booked_count(db_session):
    """CAP-05: Conflict surfaced if staffing reduction would overbook existing bookings."""
    office_id = uuid.uuid4()
    service_id = uuid.uuid4()

    office = Office(id=office_id, name="Test Office", timezone="Asia/Kolkata", is_active=True)
    service = Service(
        id=service_id,
        office_id=office_id,
        name="Test Service",
        average_service_duration_minutes=15,
        is_active=True,
    )
    db_session.add_all([office, service])
    db_session.commit()

    req1 = GenerateSlotsRequest(
        operating_date=date(2026, 11, 2),
        active_counters=4,
        start_hour=9,
        end_hour=10,
    )
    SlotGenerator.generate_slots_for_date(db_session, office_id, service_id, req1)

    # Simulate an active booking on the first slot
    slot = db_session.query(AppointmentSlot).first()
    slot.booked_count = 3
    db_session.commit()

    # Now attempt regeneration with 1 counter (which yields capacity of 1, less than booked_count 3)
    req_reduced = GenerateSlotsRequest(
        operating_date=date(2026, 11, 2),
        active_counters=1,
        start_hour=9,
        end_hour=10,
        regenerate=True,
    )
    with pytest.raises(AppError) as exc_info:
        SlotGenerator.generate_slots_for_date(db_session, office_id, service_id, req_reduced)
    assert exc_info.value.code == "CONFLICT"
