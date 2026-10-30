import uuid
from app.core.errors import AppError
from app.models.user import User
from app.models.appointment import Appointment
from app.common.dependencies import require_role


def verify_appointment_access(user: User, appointment: Appointment) -> None:
    """
    Ensure the user is authorized to read/modify this appointment.
    Citizens can ONLY access their own appointments.
    Officers/Admins can access appointments matching their assigned office.
    """
    if user.role == "CITIZEN":
        if appointment.citizen_id != user.id:
            # Return not found or forbidden without leaking appointment metadata
            raise AppError(
                status_code=404,
                code="APPOINTMENT_NOT_FOUND",
                message="Appointment not found.",
            )
        return

    if user.role in ("OFFICER", "OFFICE_ADMIN"):
        if user.office_id is not None and appointment.office_id != user.office_id:
            raise AppError(
                status_code=403,
                code="FORBIDDEN",
                message="Access forbidden for this office.",
            )
        return

    if user.role == "PLATFORM_ADMIN":
        return

    raise AppError(
        status_code=403,
        code="FORBIDDEN",
        message="Unauthorized access.",
    )
