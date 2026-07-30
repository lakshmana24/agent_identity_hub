import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal, engine, Base
from app.models.admin import Admin
from app.auth.password import hash_password
from app.repository.admin_repository import get_admin_by_email, create_admin

def seed_superadmin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@aih.dev")
        admin_password = os.getenv("ADMIN_PASSWORD", "AdminPass123!")

        existing = get_admin_by_email(db, admin_email)
        if existing:
            print(f"Superadmin '{admin_email}' already exists. Skipping creation.")
            return

        hashed = hash_password(admin_password)
        admin = create_admin(
            db=db,
            email=admin_email,
            hashed_password=hashed,
            role="superadmin",
            org_id="org_default"
        )
        print(f"Successfully seeded superadmin '{admin.email}' with ID '{admin.id}'.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_superadmin()
