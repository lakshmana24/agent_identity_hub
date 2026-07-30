import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.database.session import engine, Base, SessionLocal, get_db
from app.database.migrations import apply_auto_migrations
from app.api import (
    auth_router,
    agent_router,
    credential_router,
    governance_router,
    audit_router,
    review_router,
    dashboard_router,
    admin_router,
    chatbot_router
)
from app.middleware.audit_middleware import AuditMiddleware
from app.repository.agent_repository import seed_default_scopes
from app.scheduler.scheduler import start_scheduler, shutdown_scheduler
from app.config.settings import settings
from app.ai.gemini_client import get_ai_client, LiveGeminiClient
import app.models  # Ensures models are imported for Base.metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apply safe column migrations and ensure tables exist
    try:
        apply_auto_migrations(engine)
    except Exception as e:
        print(f"Auto-migration warning: {e}")

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
app.include_router(admin_router.router)
app.include_router(chatbot_router.router)

@app.get("/health")
@app.head("/health")
def health_check(db=Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    ai_client = get_ai_client()
    is_live_ai = isinstance(ai_client, LiveGeminiClient)

    return {
        "status": "ok" if db_ok else "error",
        "db": "connected" if db_ok else "disconnected",
        "ai_mode": "live" if is_live_ai else "mock"
    }

@app.get("/ai/status")
def ai_status():
    ai_client = get_ai_client()
    is_live_ai = isinstance(ai_client, LiveGeminiClient)
    live_ping = None
    if is_live_ai:
        live_ping = ai_client.test_live_connection()

    return {
        "ai_mode": "live" if is_live_ai else "mock",
        "configured_mode": settings.AI_MODE,
        "gemini_api_key_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "replace_with_your_gemini_api_key"),
        "live_ping": live_ping
    }

# Serve React SPA build static files if present
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
