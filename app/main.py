from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.session import engine, Base, SessionLocal, get_db
from app.api import auth_router, agent_router, credential_router, governance_router, audit_router, review_router, dashboard_router
from app.middleware.audit_middleware import AuditMiddleware
from app.repository.agent_repository import seed_default_scopes
from app.scheduler.scheduler import start_scheduler, shutdown_scheduler
import app.models  # Ensures models are imported for Base.metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_scopes(db)
    finally:
        db.close()

    # Start background scheduler
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()

app = FastAPI(title="Agent Identity Hub", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit Middleware
app.add_middleware(AuditMiddleware)

# Routers
app.include_router(auth_router.router)
app.include_router(agent_router.router)
app.include_router(credential_router.router)
app.include_router(governance_router.router)
app.include_router(audit_router.router)
app.include_router(review_router.router)
app.include_router(dashboard_router.router)

@app.get("/health")
def health_check(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
