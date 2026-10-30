import uuid
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.dependencies import require_role
from app.schemas.catalogue import (
    OfficeResponse,
    ServiceResponse,
    SlotAvailabilityResponse,
    GenerateSlotsRequest,
    GenerateSlotsResponse,
)
from app.modules.catalogue.service import CatalogueService

router = APIRouter(tags=["Office Catalogue & Slots"])


@router.get("/offices", response_model=List[OfficeResponse])
def get_offices(db: Session = Depends(get_db)):
    """List all active offices."""
    return CatalogueService.list_active_offices(db)


@router.get("/offices/{office_id}/services", response_model=List[ServiceResponse])
def get_office_services(office_id: uuid.UUID, db: Session = Depends(get_db)):
    """List active services available at a specific office."""
    return CatalogueService.list_office_services(db, office_id)


@router.get("/offices/{office_id}/services/{service_id}/slots", response_model=List[SlotAvailabilityResponse])
def get_slots(
    office_id: uuid.UUID,
    service_id: uuid.UUID,
    date: date = Query(..., description="Operating date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """List persisted slots and current availability for a specific service and date."""
    return CatalogueService.list_slots(db, office_id, service_id, date)


@router.post(
    "/admin/offices/{office_id}/services/{service_id}/slots/generate",
    response_model=GenerateSlotsResponse,
    dependencies=[Depends(require_role("OFFICE_ADMIN", "PLATFORM_ADMIN"))],
)
def generate_slots(
    office_id: uuid.UUID,
    service_id: uuid.UUID,
    payload: GenerateSlotsRequest,
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to generate persisted slots for a given date."""
    return CatalogueService.generate_slots(db, office_id, service_id, payload)
