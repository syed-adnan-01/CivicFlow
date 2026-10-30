import math
import uuid
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.appointment_slot import AppointmentSlot
from app.schemas.catalogue import GenerateSlotsRequest, GenerateSlotsResponse


class SlotGenerator:
    @staticmethod
    def calculate_block_capacities(
        active_counters: int,
        service_duration_minutes: int,
        slot_duration_minutes: int,
        walk_in_share: float,
    ) -> List[int]:
        """
        Calculates persisted capacity for each slot in a 60-minute block
        according to the QueueLess 2.3 specification:
        - block_capacity = active_counters * floor(60 / service_duration_minutes)
        - walk_in_reserve = floor(block_capacity * walk_in_share)
        - appointment_block_capacity = block_capacity - walk_in_reserve
        - chronological quotient/remainder distribution across slots.
        """
        if service_duration_minutes <= 0 or slot_duration_minutes <= 0:
            raise ValueError("Service and slot durations must be positive.")
        if active_counters <= 0:
            slots_in_block = 60 // slot_duration_minutes
            return [0] * slots_in_block

        services_per_counter_hour = 60 // service_duration_minutes
        block_capacity = active_counters * services_per_counter_hour
        walk_in_reserve = math.floor(block_capacity * walk_in_share)
        appointment_block_capacity = max(0, block_capacity - walk_in_reserve)

        slots_in_block = 60 // slot_duration_minutes
        if slots_in_block <= 0:
            raise ValueError("Slot duration cannot exceed 60 minutes.")

        base = appointment_block_capacity // slots_in_block
        remainder = appointment_block_capacity % slots_in_block

        capacities = []
        for i in range(slots_in_block):
            slot_cap = base + 1 if i < remainder else base
            capacities.append(slot_cap)

        return capacities

    @classmethod
    def generate_slots_for_date(
        cls,
        db: Session,
        office_id: uuid.UUID,
        service_id: uuid.UUID,
        params: GenerateSlotsRequest,
    ) -> GenerateSlotsResponse:
        office = db.query(Office).filter_by(id=office_id).first()
        if not office or not office.is_active:
            raise AppError(status_code=404, code="NOT_FOUND", message="Active office not found.")

        service = db.query(Service).filter_by(id=service_id, office_id=office_id).first()
        if not service or not service.is_active:
            raise AppError(status_code=404, code="NOT_FOUND", message="Active service not found for this office.")

        # Load effective policy
        policy = (
            db.query(QueuePolicy)
            .filter(
                QueuePolicy.office_id == office_id,
                QueuePolicy.service_id.in_([service_id, None]),
            )
            .order_by(QueuePolicy.service_id.desc(), QueuePolicy.policy_version.desc())
            .first()
        )
        if not policy:
            # Fallback default policy
            slot_duration = 15
            walk_in_share = 0.20
            policy_version = 1
        else:
            slot_duration = policy.slot_duration_minutes
            walk_in_share = policy.walk_in_share
            policy_version = policy.policy_version

        tz = ZoneInfo(office.timezone)
        op_date = params.operating_date
        total_slots = 0
        open_slots = 0
        closed_slots = 0

        # Iterate operating hours block by block
        for hour in range(params.start_hour, params.end_hour):
            is_break = False
            if (
                params.break_start_hour is not None
                and params.break_end_hour is not None
                and params.break_start_hour <= hour < params.break_end_hour
            ):
                is_break = True

            block_start_local = datetime.combine(op_date, time(hour, 0), tzinfo=tz)
            block_start_utc = block_start_local.astimezone(ZoneInfo("UTC"))

            if is_break:
                capacities = [0] * (60 // slot_duration)
            else:
                capacities = cls.calculate_block_capacities(
                    active_counters=params.active_counters,
                    service_duration_minutes=service.average_service_duration_minutes,
                    slot_duration_minutes=slot_duration,
                    walk_in_share=walk_in_share,
                )

            slots_in_block = len(capacities)
            for i, cap in enumerate(capacities):
                slot_start_local = block_start_local + timedelta(minutes=i * slot_duration)
                slot_end_local = slot_start_local + timedelta(minutes=slot_duration)
                slot_start_utc = slot_start_local.astimezone(ZoneInfo("UTC"))
                slot_end_utc = slot_end_local.astimezone(ZoneInfo("UTC"))

                status = "OPEN" if cap > 0 and not is_break else "CLOSED"

                # Check if slot already exists
                existing_slot = (
                    db.query(AppointmentSlot)
                    .filter_by(
                        office_id=office_id,
                        service_id=service_id,
                        starts_at=slot_start_utc,
                    )
                    .first()
                )

                if existing_slot:
                    if not params.regenerate:
                        continue  # Idempotent skip
                    # Never silently reduce capacity below confirmed booked_count
                    if cap < existing_slot.booked_count:
                        raise AppError(
                            status_code=409,
                            code="CONFLICT",
                            message=f"Cannot reduce slot capacity to {cap} because {existing_slot.booked_count} bookings already exist.",
                        )
                    existing_slot.capacity = cap
                    existing_slot.capacity_policy_version = policy_version
                    existing_slot.status = "FULL" if existing_slot.booked_count >= cap else status
                else:
                    new_slot = AppointmentSlot(
                        id=uuid.uuid4(),
                        office_id=office_id,
                        service_id=service_id,
                        starts_at=slot_start_utc,
                        ends_at=slot_end_utc,
                        operating_date=op_date,
                        block_start_at=block_start_utc,
                        capacity=cap,
                        booked_count=0,
                        status=status,
                        capacity_policy_version=policy_version,
                    )
                    db.add(new_slot)

                total_slots += 1
                if status == "OPEN":
                    open_slots += 1
                else:
                    closed_slots += 1

        db.commit()

        return GenerateSlotsResponse(
            message="Slots generation completed successfully.",
            operating_date=op_date,
            total_slots_generated=total_slots,
            open_slots=open_slots,
            closed_slots=closed_slots,
        )
