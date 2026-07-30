from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin, require_superadmin, require_write_access
from app.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentUpdateRequest,
    IdentityCard,
    AgentListResponse,
    ScopeCreateRequest,
    ScopeResponse
)
from app.services.identity_service import (
    register_agent_service,
    get_agent_detail_service,
    list_agents_service,
    update_agent_service,
    soft_delete_agent_service
)
from app.repository.agent_repository import (
    get_all_scopes,
    create_scope,
    get_scope_by_id_or_name,
    delete_or_deprecate_scope
)
from app.models.admin import Admin

router = APIRouter(tags=["Identity & Agent Management"])

@router.post("/agents", response_model=IdentityCard, status_code=status.HTTP_201_CREATED)
def register_agent(
    payload: AgentCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_write_access)
):
    return register_agent_service(db, payload)

@router.get("/agents", response_model=AgentListResponse)
def list_agents(
    status: Optional[str] = Query(None, description="Filter by lifecycle status (active, suspended, deprovisioned)"),
    owning_team: Optional[str] = Query(None, description="Filter by owning team (Growth, Finance, DevOps, Logistics, Support)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (Low, Medium, High, Critical)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return list_agents_service(db, status=status, owning_team=owning_team, risk_level=risk_level, page=page, page_size=page_size)

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
    current_admin: Admin = Depends(require_write_access)
):
    return update_agent_service(db, id, payload)

@router.delete("/agents/{id}")
def delete_agent(
    id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_superadmin)
):
    return soft_delete_agent_service(db, id)

# --- Runtime Scope Manifest Endpoints ---

@router.get("/scopes", response_model=List[ScopeResponse])
def list_scopes(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return get_all_scopes(db)

@router.post("/scopes", response_model=ScopeResponse, status_code=status.HTTP_201_CREATED)
def create_new_scope(
    payload: ScopeCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_superadmin)
):
    existing = get_scope_by_id_or_name(db, payload.scope_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scope '{payload.scope_name}' already exists in manifest."
        )

    if payload.action_type not in ("read", "write"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action_type must be 'read' or 'write'."
        )

    new_scope = create_scope(db, {
        "scope_name": payload.scope_name,
        "action_type": payload.action_type,
        "description": payload.description,
        "risk_level": payload.risk_level
    })
    return ScopeResponse.model_validate(new_scope)

@router.delete("/scopes/{id_or_name}")
def remove_or_deprecate_scope(
    id_or_name: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_superadmin)
):
    scope = get_scope_by_id_or_name(db, id_or_name)
    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scope '{id_or_name}' not found."
        )

    result = delete_or_deprecate_scope(db, scope)
    if getattr(result, "deprecated", False):
        return {"status": "deprecated", "scope_name": scope.scope_name, "message": "Scope is in active use by agents. Marked as deprecated to prevent new grants while keeping existing grants valid."}
    return {"status": "deleted", "scope_name": scope.scope_name}
