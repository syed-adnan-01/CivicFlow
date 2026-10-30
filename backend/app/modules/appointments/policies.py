"""
Appointment business policies and cutoff evaluation.
"""
from datetime import datetime
from app.core.time import utc_now, ensure_utc
from app.models.appointment import Appointment


def is_appointment_cancellable(appointment: Appointment, now: datetime = None) -> bool:
    """Validate that appointment is in BOOKED state and before cutoff."""
    if appointment.status != "BOOKED":
        return False
    current_time = now or utc_now()
    # By default, must be before check-in close
    return current_time <= ensure_utc(appointment.check_in_close_at)
