import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class BookAppointmentRequest(BaseModel):
    slot_id: uuid.UUID
    service_id: uuid.UUID


class AppointmentDetailResponse(BaseModel):
    id: uuid.UUID
    citizen_id: uuid.UUID
    office_id: uuid.UUID
    service_id: uuid.UUID
    slot_id: uuid.UUID
    status: str
    booking_reference: Optional[str] = None
    slot_start_at: datetime
    check_in_open_at: datetime
    check_in_close_at: datetime
    rescheduled_from_id: Optional[uuid.UUID] = None
    rescheduled_to_id: Optional[uuid.UUID] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    qr_rotated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookAppointmentResponse(BaseModel):
    appointment: AppointmentDetailResponse
    qr_reference: str  # Raw 256-bit opaque reference returned once


class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = "Citizen requested cancellation"


class RescheduleAppointmentRequest(BaseModel):
    new_slot_id: uuid.UUID


class RotateQRResponse(BaseModel):
    qr_reference: str
    rotated_at: datetime
    expires_at: datetime
