import argparse
import sys
import os
import uuid

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.user import User


def create_user(firebase_uid: str, phone: str, display_name: str, role: str, office_id_str: str = None):
    db = SessionLocal()
    try:
        office_id = uuid.UUID(office_id_str) if office_id_str else None
        existing = db.query(User).filter_by(firebase_uid=firebase_uid).first()
        if existing:
            print(f"User with firebase_uid '{firebase_uid}' already exists with role '{existing.role}'.")
            return

        user = User(
            id=uuid.uuid4(),
            firebase_uid=firebase_uid,
            phone_number=phone,
            display_name=display_name,
            role=role.upper(),
            office_id=office_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"User created: ID={user.id}, UID={user.firebase_uid}, Role={user.role}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a QueueLess user profile")
    parser.add_argument("--uid", required=True, help="Firebase UID")
    parser.add_argument("--phone", default=None, help="Phone number with country code")
    parser.add_argument("--name", default="Demo User", help="Display name")
    parser.add_argument("--role", default="CITIZEN", choices=["CITIZEN", "OFFICER", "OFFICE_ADMIN", "PLATFORM_ADMIN"])
    parser.add_argument("--office-id", default=None, help="UUID of assigned office for staff")

    args = parser.parse_args()
    create_user(args.uid, args.phone, args.name, args.role, args.office_id)
