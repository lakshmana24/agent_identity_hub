import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal, engine, Base
from app.models.admin import Admin
from app.auth.password import hash_password
from app.repository.admin_repository import get_admin_by_email, create_admin

DEMO_ACCOUNTS = [
    {"email": "admin@aih.dev", "password": "AdminPass123!", "role": "superadmin"},
    {"email": "operator@aih.dev", "password": "OperatorPass123!", "role": "admin"},
    {"email": "auditor@aih.dev", "password": "AuditorPass123!", "role": "auditor"},
]

def seed_demo_admins():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for acc in DEMO_ACCOUNTS:
            existing = get_admin_by_email(db, acc["email"])
            if existing:
                print(f"Account '{acc['email']}' already exists. Skipping.")
                continue

            hashed = hash_password(acc["password"])
            admin = create_admin(
                db=db,
                email=acc["email"],
                hashed_password=hashed,
                role=acc["role"],
                org_id="org_default"
            )
            print(f"Successfully seeded '{acc['role']}' account '{admin.email}' with ID '{admin.id}'.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_admins()
