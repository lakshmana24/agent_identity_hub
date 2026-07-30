from datetime import datetime, timedelta, timezone
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
from app.ai.gemini_client import get_ai_client

RISK_HIERARCHY = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
RISK_REVERSE = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}

def _calculate_risk_from_scopes(scopes_manifest) -> tuple[str, str]:
    max_risk_num = 1
    highest_scope = "crm:read"
    for s in scopes_manifest:
        risk_num = RISK_HIERARCHY.get(s.risk_level, 1)
        if risk_num > max_risk_num:
            max_risk_num = risk_num
            highest_scope = s.scope_name

    risk_str = RISK_REVERSE.get(max_risk_num, "Low")
    if risk_str == "Critical":
        reasoning = f"Agent has critical permission ({highest_scope}), which allows executing sensitive financial transactions or administrative control."
    elif risk_str == "High":
        reasoning = f"Agent holds high-privilege permission ({highest_scope}), allowing modification of core enterprise inventory or data."
    elif risk_str == "Medium":
        reasoning = f"Agent holds write permissions ({highest_scope}), allowing modification of operational records."
    else:
        reasoning = "Agent operates under minimal read-only permissions with low security risk."

    return risk_str, reasoning

def build_identity_card(db: Session, agent: Agent) -> IdentityCard:
    cred = get_latest_credential_by_agent_id(db, agent.id)
    cred_status = "not_issued"
    active_cred_exp = None

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
        active_cred_exp = exp

    # Check agent identity authorized lifetime expiry_date
    agent_exp = agent.expiry_date
    if agent_exp and agent_exp.tzinfo is None:
        agent_exp = agent_exp.replace(tzinfo=timezone.utc)

    return IdentityCard(
        agent_id=agent.id,
        agent_name=agent.agent_name,
        owning_team=getattr(agent, "owning_team", "Growth") or "Growth",
        purpose=agent.purpose,
        owner=agent.owner or "admin@company.com",
        expiry_date=agent_exp,
        model_provider=agent.model_provider or "Other",
        model_name=agent.model_name or "unknown",
        tools=agent.tools or [],
        agent_endpoint_url=agent.agent_endpoint_url,
        deployment_environment=agent.deployment_environment or "production",
        description=agent.description,
        risk_level=agent.risk_level,
        risk_level_source=agent.risk_level_source or "ai_recommended",
        risk_reasoning=getattr(agent, "risk_reasoning", None) or f"Assigned {agent.risk_level} risk level based on granted tool scopes.",
        allowed_scopes=agent.allowed_scopes or [],
        credential_status=cred_status,
        active_credential_expires_at=active_cred_exp,
        lifecycle_status=agent.lifecycle_status,
        security_score=agent.security_score,
        flagged_for_review=agent.flagged_for_review,
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

    # 2. Determine risk level & specific reasoning
    calc_risk, calc_reasoning = _calculate_risk_from_scopes(found_scopes)
    if payload.risk_level and payload.risk_level in RISK_HIERARCHY:
        final_risk = payload.risk_level
        risk_source = payload.risk_level_source or "admin_override"
        risk_reasoning = payload.risk_reasoning or f"Admin overridden to {final_risk} risk."
    else:
        # Call AI client for grounded recommendation reasoning if available
        ai_client = get_ai_client()
        rec = ai_client.recommend_scopes(payload.purpose, found_scopes, payload.model_provider or "Other", payload.model_name or "unknown", payload.tools or [])
        final_risk = rec.risk_level or calc_risk
        risk_reasoning = rec.reasoning or calc_reasoning
        risk_source = "ai_recommended"

    # 3. Resolve agent identity authorized lifetime expiry_date (default 1 year)
    now = datetime.now(timezone.utc)
    if payload.expiry_date:
        agent_exp = payload.expiry_date if payload.expiry_date.tzinfo else payload.expiry_date.replace(tzinfo=timezone.utc)
    else:
        agent_exp = now + timedelta(days=365)

    # 4. Create agent record
    agent_data = {
        "agent_name": payload.agent_name,
        "owning_team": payload.owning_team,
        "purpose": payload.purpose,
        "owner": payload.owner or "admin@company.com",
        "expiry_date": agent_exp,
        "model_provider": payload.model_provider or "Other",
        "model_name": payload.model_name or "unknown",
        "tools": payload.tools or [],
        "agent_endpoint_url": payload.agent_endpoint_url,
        "deployment_environment": payload.deployment_environment or "production",
        "description": payload.description,
        "risk_level": final_risk,
        "risk_level_source": risk_source,
        "risk_reasoning": risk_reasoning,
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
    owning_team: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> AgentListResponse:
    agents, total = get_agents(db, status=status, owning_team=owning_team, risk_level=risk_level, page=page, page_size=page_size)
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
        if "risk_level" not in update_dict:
            calc_risk, calc_reasoning = _calculate_risk_from_scopes(found_scopes)
            update_dict["risk_level"] = calc_risk
            update_dict["risk_reasoning"] = calc_reasoning

    updated_agent = repo_update_agent(db, agent, update_dict)
    return build_identity_card(db, updated_agent)

def soft_delete_agent_service(db: Session, agent_id: str) -> dict:
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")

    repo_update_agent(db, agent, {"lifecycle_status": "deprovisioned"})
    deactivate_agent_credentials(db, agent_id, rotated=False, reason="Agent deprovisioned")
    return {"status": "deprovisioned", "agent_id": agent_id}
