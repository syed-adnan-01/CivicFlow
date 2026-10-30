import uuid
import sys
import os
from datetime import datetime, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.core.time import utc_now
from app.models.office import Office
from app.models.service import Service
from app.models.queue_policy import QueuePolicy
from app.models.user import User

# Stable demo UUIDs so tests and teammates can reference predictable IDs
DEMO_OFFICE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_SERVICE_INCOME_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DEMO_SERVICE_CASTE_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
DEMO_CITIZEN_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
DEMO_OFFICER_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
DEMO_ADMIN_ID = uuid.UUID("66666666-6666-6666-6666-666666666666")


def seed_data():
    db = SessionLocal()
    try:
        print("Starting demo data seed...")

        # 1. Office
        office = db.query(Office).filter_by(id=DEMO_OFFICE_ID).first()
        if not office:
            office = Office(
                id=DEMO_OFFICE_ID,
                name="Bengaluru Urban Tahsildar Office",
                address="Kandaya Bhavana, KG Road, Bengaluru, Karnataka 560009",
                timezone="Asia/Kolkata",
                is_active=True,
            )
            db.add(office)
            print("  Created demo office: Bengaluru Urban Tahsildar Office")

        # 2. Services
        service_income = db.query(Service).filter_by(id=DEMO_SERVICE_INCOME_ID).first()
        if not service_income:
            service_income = Service(
                id=DEMO_SERVICE_INCOME_ID,
                office_id=DEMO_OFFICE_ID,
                name="Income Certificate Verification",
                description="Document verification and token issuance for annual income certificate application.",
                average_service_duration_minutes=10,
                is_active=True,
            )
            db.add(service_income)
            print("  Created service: Income Certificate Verification (10 min)")

        service_caste = db.query(Service).filter_by(id=DEMO_SERVICE_CASTE_ID).first()
        if not service_caste:
            service_caste = Service(
                id=DEMO_SERVICE_CASTE_ID,
                office_id=DEMO_OFFICE_ID,
                name="Caste Certificate Verification",
                description="Document verification and verification for SC/ST/OBC certificate application.",
                average_service_duration_minutes=15,
                is_active=True,
            )
            db.add(service_caste)
            print("  Created service: Caste Certificate Verification (15 min)")

        # 3. Default Queue Policy
        policy = db.query(QueuePolicy).filter_by(office_id=DEMO_OFFICE_ID, service_id=None).first()
        if not policy:
            policy = QueuePolicy(
                office_id=DEMO_OFFICE_ID,
                service_id=None,
                slot_duration_minutes=15,
                walk_in_share=0.20,
                max_walk_in_wait_minutes=60,
                checkin_open_minutes=15,
                checkin_close_minutes=10,
                policy_version=1,
                effective_from=utc_now(),
            )
            db.add(policy)
            print("  Created office default queue policy (v1)")

        # 4. Users (Citizen, Officer, Admin)
        citizen = db.query(User).filter_by(firebase_uid="citizen-demo-uid").first()
        if not citizen:
            citizen = User(
                id=DEMO_CITIZEN_ID,
                firebase_uid="citizen-demo-uid",
                phone_number="+919876543210",
                display_name="Ramesh Kumar",
                role="CITIZEN",
                is_active=True,
            )
            db.add(citizen)
            print("  Created demo citizen: Ramesh Kumar (+919876543210)")

        officer = db.query(User).filter_by(firebase_uid="officer-demo-uid").first()
        if not officer:
            officer = User(
                id=DEMO_OFFICER_ID,
                firebase_uid="officer-demo-uid",
                phone_number="+919876543211",
                display_name="Suresh Verma (Officer)",
                role="OFFICER",
                office_id=DEMO_OFFICE_ID,
                is_active=True,
            )
            db.add(officer)
            print("  Created demo officer: Suresh Verma")

        admin = db.query(User).filter_by(firebase_uid="admin-demo-uid").first()
        if not admin:
            admin = User(
                id=DEMO_ADMIN_ID,
                firebase_uid="admin-demo-uid",
                phone_number="+919876543212",
                display_name="Priya Sharma (Office Admin)",
                role="OFFICE_ADMIN",
                office_id=DEMO_OFFICE_ID,
                is_active=True,
            )
            db.add(admin)
            print("  Created demo office admin: Priya Sharma")

        db.commit()
        print("Demo seed completed successfully.")
    except Exception as exc:
        db.rollback()
        print("Error seeding demo data:", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
