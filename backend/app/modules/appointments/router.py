import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.appointment import (
    BookAppointmentRequest,
    BookAppointmentResponse,
    AppointmentDetailResponse,
    CancelAppointmentRequest,
    RescheduleAppointmentRequest,
    RotateQRResponse,
)
from app.modules.appointments.service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments Lifecycle"])


@router.post("", response_model=BookAppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: BookAppointmentRequest,
    response: Response,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_role("CITIZEN")),
    db: Session = Depends(get_db),
):
    """
    Book an appointment for an active citizen in an open slot.
    Returns appointment details and a raw 256-bit QR reference once.
    """
    # Enforce no-store on sensitive QR response
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    booking_result, is_cached = AppointmentService.book_appointment(
        db=db,
        user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
    )
    return booking_result


@router.get("", response_model=List[AppointmentDetailResponse])
def list_my_appointments(
    current_user: User = Depends(require_role("CITIZEN")),
    db: Session = Depends(get_db),
):
    """List authenticated citizen's appointments (citizens can access ONLY their own)."""
    return AppointmentService.list_my_appointments(db, current_user)


@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get appointment detail. Accessible to citizen owner or authorized office staff."""
    return AppointmentService.get_appointment_detail(db, appointment_id, current_user)


@router.post("/{appointment_id}/cancel", response_model=AppointmentDetailResponse)
def cancel_appointment(
    appointment_id: uuid.UUID,
    payload: CancelAppointmentRequest = CancelAppointmentRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an active appointment and release reserved slot capacity."""
    return AppointmentService.cancel_appointment(db, appointment_id, current_user, payload)


@router.post("/{appointment_id}/reschedule", response_model=BookAppointmentResponse)
def reschedule_appointment(
    appointment_id: uuid.UUID,
    payload: RescheduleAppointmentRequest,
    response: Response,
    current_user: User = Depends(require_role("CITIZEN")),
    db: Session = Depends(get_db),
):
    """
    Reschedule an active appointment to a new slot.
    Atomically decrements old slot and reserves new slot.
    Issues a new raw QR reference and invalidates old references.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return AppointmentService.reschedule_appointment(db, appointment_id, current_user, payload)


@router.post("/{appointment_id}/qr/rotate", response_model=RotateQRResponse)
def rotate_qr(
    appointment_id: uuid.UUID,
    response: Response,
    current_user: User = Depends(require_role("CITIZEN")),
    db: Session = Depends(get_db),
):
    """
    Rotate QR reference for an active appointment.
    Invalidates previous unused references and issues a new reference.
    Rate-limited to prevent abuse.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return AppointmentService.rotate_qr(db, appointment_id, current_user)
