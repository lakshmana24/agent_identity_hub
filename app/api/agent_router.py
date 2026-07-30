from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin, require_role
from app.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentUpdateRequest,
    IdentityCard,
    AgentListResponse,
    ScopeResponse
)
from app.services.identity_service import (
    register_agent_service,
    get_agent_detail_service,
    list_agents_service,
    update_agent_service,
    soft_delete_agent_service
)
from app.repository.agent_repository import get_all_scopes
from app.models.admin import Admin

router = APIRouter(tags=["Identity & Agent Management"])

@router.post("/agents", response_model=IdentityCard, status_code=status.HTTP_201_CREATED)
def register_agent(
    payload: AgentCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return register_agent_service(db, payload)

@router.get("/agents", response_model=AgentListResponse)
def list_agents(
    status: Optional[str] = Query(None, description="Filter by lifecycle status (active, suspended, deprovisioned)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (Low, Medium, High, Critical)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return list_agents_service(db, status=status, department=department, risk_level=risk_level, page=page, page_size=page_size)

@router.get("/agents/{id}", response_model=IdentityCard)
def get_agent(
    id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return get_agent_detail_service(db, id)

@router.put("/agents/{id}", response_model=IdentityCard)
def update_agent(
    id: str,
    payload: AgentUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return update_agent_service(db, id, payload)

@router.delete("/agents/{id}")
def delete_agent(
    id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role("superadmin"))
):
    return soft_delete_agent_service(db, id)

@router.get("/scopes", response_model=List[ScopeResponse])
def list_scopes(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return get_all_scopes(db)
