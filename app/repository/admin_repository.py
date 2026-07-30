from sqlalchemy.orm import Session
from app.models.admin import Admin

def get_admin_by_email(db: Session, email: str) -> Admin | None:
    return db.query(Admin).filter(Admin.email == email.lower()).first()

def get_admin_by_id(db: Session, admin_id: str) -> Admin | None:
    return db.query(Admin).filter(Admin.id == admin_id).first()

def create_admin(db: Session, email: str, hashed_password: str, role: str = "admin", org_id: str = "org_default") -> Admin:
    admin = Admin(
        email=email.lower(),
        hashed_password=hashed_password,
        role=role,
        org_id=org_id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
