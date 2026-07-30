from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.scope_manifest import ScopeManifest

# --- Scope Manifest Repository Functions ---

DEFAULT_SCOPES = [
    {"scope_name": "crm:read", "action_type": "read", "description": "Read access to customer relationship management data", "risk_level": "Low"},
    {"scope_name": "crm:write", "action_type": "write", "description": "Create and modify customer records in CRM", "risk_level": "Medium"},
    {"scope_name": "tickets:read", "action_type": "read", "description": "Read access to support tickets and customer queries", "risk_level": "Low"},
    {"scope_name": "tickets:write", "action_type": "write", "description": "Create, update, and resolve support tickets", "risk_level": "Medium"},
    {"scope_name": "inventory:read", "action_type": "read", "description": "Read access to stock levels and product inventory", "risk_level": "Low"},
    {"scope_name": "inventory:write", "action_type": "write", "description": "Modify inventory counts, product listings, and orders", "risk_level": "High"},
    {"scope_name": "payments:read", "action_type": "read", "description": "Read transaction history and payment status", "risk_level": "Medium"},
    {"scope_name": "payments:write", "action_type": "write", "description": "Process refunds and initiate payment transactions", "risk_level": "Critical"},
]

def seed_default_scopes(db: Session) -> None:
    for s in DEFAULT_SCOPES:
        existing = db.query(ScopeManifest).filter(ScopeManifest.scope_name == s["scope_name"]).first()
        if not existing:
            db.add(ScopeManifest(**s))
    db.commit()

def get_all_scopes(db: Session) -> List[ScopeManifest]:
    return db.query(ScopeManifest).order_by(ScopeManifest.scope_name).all()

def get_scopes_by_names(db: Session, scope_names: List[str]) -> List[ScopeManifest]:
    return db.query(ScopeManifest).filter(ScopeManifest.scope_name.in_(scope_names)).all()

def get_scope_by_id_or_name(db: Session, identifier: str) -> Optional[ScopeManifest]:
    return db.query(ScopeManifest).filter(
        (ScopeManifest.id == identifier) | (ScopeManifest.scope_name == identifier)
    ).first()

def create_scope(db: Session, scope_data: dict) -> ScopeManifest:
    scope = ScopeManifest(**scope_data)
    db.add(scope)
    db.commit()
    db.refresh(scope)
    return scope

def delete_or_deprecate_scope(db: Session, scope: ScopeManifest) -> ScopeManifest:
    active_agents = db.query(Agent).filter(Agent.lifecycle_status != "deprovisioned").all()
    in_use = any(scope.scope_name in (a.allowed_scopes or []) for a in active_agents)

    if in_use:
        scope.deprecated = True
        db.commit()
        db.refresh(scope)
        return scope
    else:
        db.delete(scope)
        db.commit()
        return scope


# --- Agent Repository Functions ---

def get_agent_by_id(db: Session, agent_id: str) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.id == agent_id).first()

def get_agents(
    db: Session,
    status: Optional[str] = None,
    owning_team: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Agent], int]:
    query = db.query(Agent)

    if status:
        query = query.filter(Agent.lifecycle_status == status)
    else:
        query = query.filter(Agent.lifecycle_status != "deprovisioned")

    if owning_team:
        query = query.filter(Agent.owning_team == owning_team)

    if risk_level:
        query = query.filter(Agent.risk_level == risk_level)

    total = query.count()
    agents = query.order_by(Agent.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return agents, total

def create_agent(db: Session, agent_data: dict) -> Agent:
    agent = Agent(**agent_data)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

def update_agent(db: Session, agent: Agent, update_dict: dict) -> Agent:
    for key, value in update_dict.items():
        if value is not None:
            setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return agent
