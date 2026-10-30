import uuid
from datetime import date
from typing import List
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.office import Office
from app.models.service import Service
from app.models.appointment_slot import AppointmentSlot
from app.schemas.catalogue import (
    OfficeResponse,
    ServiceResponse,
    SlotAvailabilityResponse,
    GenerateSlotsRequest,
    GenerateSlotsResponse,
)
from app.modules.appointments.slot_generator import SlotGenerator


class CatalogueService:
    @staticmethod
    def list_active_offices(db: Session) -> List[OfficeResponse]:
        offices = db.query(Office).filter(Office.is_active.is_(True)).order_by(Office.name).all()
        return [OfficeResponse.model_validate(o) for o in offices]

    @staticmethod
    def list_office_services(db: Session, office_id: uuid.UUID) -> List[ServiceResponse]:
        services = (
            db.query(Service)
            .filter(Service.office_id == office_id, Service.is_active.is_(True))
            .order_by(Service.name)
            .all()
        )
        return [ServiceResponse.model_validate(s) for s in services]

    @staticmethod
    def list_slots(
        db: Session,
        office_id: uuid.UUID,
        service_id: uuid.UUID,
        operating_date: date,
    ) -> List[SlotAvailabilityResponse]:
        slots = (
            db.query(AppointmentSlot)
            .filter(
                AppointmentSlot.office_id == office_id,
                AppointmentSlot.service_id == service_id,
                AppointmentSlot.operating_date == operating_date,
            )
            .order_by(AppointmentSlot.starts_at)
            .all()
        )

        response = []
        for s in slots:
            available = max(0, s.capacity - s.booked_count)
            response.append(
                SlotAvailabilityResponse(
                    id=s.id,
                    office_id=s.office_id,
                    service_id=s.service_id,
                    operating_date=s.operating_date,
                    starts_at=s.starts_at,
                    ends_at=s.ends_at,
                    capacity=s.capacity,
                    booked_count=s.booked_count,
                    available_count=available,
                    status=s.status,
                    capacity_policy_version=s.capacity_policy_version,
                )
            )
        return response

    @staticmethod
    def generate_slots(
        db: Session,
        office_id: uuid.UUID,
        service_id: uuid.UUID,
        params: GenerateSlotsRequest,
    ) -> GenerateSlotsResponse:
        return SlotGenerator.generate_slots_for_date(db, office_id, service_id, params)
