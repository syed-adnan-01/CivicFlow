import pytest
from sqlalchemy import create_engine
from app.core.database import Base
from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.user import User
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.checkin_reference import CheckinReference
from app.models.idempotency_key import IdempotencyKey
from app.models.audit_event import AuditEvent


def test_models_metadata_complete():
    expected_tables = {
        "users",
        "offices",
        "services",
        "queue_policy",
        "appointment_slots",
        "appointments",
        "checkin_references",
        "idempotency_keys",
        "audit_events",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_sqlite_in_memory_ddl():
    # Verify tables can be created on a test engine
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    assert "users" in Base.metadata.tables
    assert "appointments" in Base.metadata.tables
    assert "checkin_references" in Base.metadata.tables
