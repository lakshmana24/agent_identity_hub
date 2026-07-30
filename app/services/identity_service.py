from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentUpdateRequest,
    IdentityCard,
    AgentListResponse
)
from app.repository.agent_repository import (
    get_agent_by_id,
    get_agents,
    create_agent as repo_create_agent,
    update_agent as repo_update_agent,
    get_scopes_by_names,
    get_all_scopes
)
from app.repository.credential_repository import get_latest_credential_by_agent_id, deactivate_agent_credentials
from app.models.agent import Agent

RISK_HIERARCHY = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
RISK_REVERSE = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}

def _calculate_risk_from_scopes(scopes_manifest) -> str:
    max_risk_num = 1
    for s in scopes_manifest:
        risk_num = RISK_HIERARCHY.get(s.risk_level, 1)
        if risk_num > max_risk_num:
            max_risk_num = risk_num
    return RISK_REVERSE.get(max_risk_num, "Low")

def build_identity_card(db: Session, agent: Agent) -> IdentityCard:
    cred = get_latest_credential_by_agent_id(db, agent.id)
    cred_status = "not_issued"
    exp_date = None

    if cred:
        now = datetime.now(timezone.utc)
        exp = cred.expires_at
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if not cred.active:
            cred_status = "revoked"
        elif exp and exp < now:
            cred_status = "expired"
        else:
            cred_status = "active"
        exp_date = exp

    return IdentityCard(
        agent_id=agent.id,
        agent_name=agent.agent_name,
        purpose=agent.purpose,
        department=agent.department,
        owner=agent.owner,
        description=agent.description,
        risk_level=agent.risk_level,
        allowed_scopes=agent.allowed_scopes or [],
        credential_status=cred_status,
        expiry_date=exp_date,
        lifecycle_status=agent.lifecycle_status,
        security_score=agent.security_score,
        flagged_for_review=agent.flagged_for_review,
        ai_summary=agent.ai_summary,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )

def register_agent_service(db: Session, payload: AgentCreateRequest) -> IdentityCard:
    # 1. Validate requested scopes
    requested_scopes = sorted(list(set(payload.requested_scopes)))
    found_scopes = get_scopes_by_names(db, requested_scopes)
    found_names = {s.scope_name for s in found_scopes}

    missing_scopes = set(requested_scopes) - found_names
    if missing_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes requested: {sorted(list(missing_scopes))}. Scope does not exist in manifest."
        )

    # 2. Determine risk level from scopes
    risk_level = _calculate_risk_from_scopes(found_scopes)

    # 3. Create agent record
    agent_data = {
        "agent_name": payload.agent_name,
        "purpose": payload.purpose,
        "department": payload.department,
        "owner": payload.owner,
        "description": payload.description,
        "risk_level": risk_level,
        "allowed_scopes": requested_scopes,
        "lifecycle_status": "active",
        "security_score": 100
    }

    agent = repo_create_agent(db, agent_data)
    return build_identity_card(db, agent)

def get_agent_detail_service(db: Session, agent_id: str) -> IdentityCard:
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")
    return build_identity_card(db, agent)

def list_agents_service(
    db: Session,
    status: Optional[str] = None,
    department: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> AgentListResponse:
    agents, total = get_agents(db, status=status, department=department, risk_level=risk_level, page=page, page_size=page_size)
    cards = [build_identity_card(db, a) for a in agents]
    return AgentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        agents=cards
    )

def update_agent_service(db: Session, agent_id: str, payload: AgentUpdateRequest) -> IdentityCard:
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")

    if agent.lifecycle_status == "deprovisioned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot update a deprovisioned agent.")

    update_dict = payload.model_dump(exclude_unset=True)

    if "requested_scopes" in update_dict:
        new_scopes = sorted(list(set(update_dict.pop("requested_scopes"))))
        found_scopes = get_scopes_by_names(db, new_scopes)
        found_names = {s.scope_name for s in found_scopes}
        missing_scopes = set(new_scopes) - found_names
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scopes requested: {sorted(list(missing_scopes))}."
            )
        update_dict["allowed_scopes"] = new_scopes
        update_dict["risk_level"] = _calculate_risk_from_scopes(found_scopes)

    updated_agent = repo_update_agent(db, agent, update_dict)
    return build_identity_card(db, updated_agent)

def soft_delete_agent_service(db: Session, agent_id: str) -> dict:
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")

    repo_update_agent(db, agent, {"lifecycle_status": "deprovisioned"})
    deactivate_agent_credentials(db, agent_id, rotated=False, reason="Agent deprovisioned")
    return {"status": "deprovisioned", "agent_id": agent_id}
