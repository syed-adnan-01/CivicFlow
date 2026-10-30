import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class OfficeResponse(BaseModel):
    id: uuid.UUID
    name: str
    address: Optional[str] = None
    timezone: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceResponse(BaseModel):
    id: uuid.UUID
    office_id: uuid.UUID
    name: str
    description: Optional[str] = None
    average_service_duration_minutes: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SlotAvailabilityResponse(BaseModel):
    id: uuid.UUID
    office_id: uuid.UUID
    service_id: uuid.UUID
    operating_date: date
    starts_at: datetime
    ends_at: datetime
    capacity: int
    booked_count: int
    available_count: int
    status: str
    capacity_policy_version: int

    model_config = ConfigDict(from_attributes=True)


class GenerateSlotsRequest(BaseModel):
    operating_date: date
    active_counters: int = 2
    start_hour: int = 9
    end_hour: int = 17
    break_start_hour: Optional[int] = 13
    break_end_hour: Optional[int] = 14
    regenerate: bool = False


class GenerateSlotsResponse(BaseModel):
    message: str
    operating_date: date
    total_slots_generated: int
    open_slots: int
    closed_slots: int
