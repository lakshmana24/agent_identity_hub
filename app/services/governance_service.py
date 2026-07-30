from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.credential import Credential
from app.schemas.governance_schemas import (
    GovernanceAnalyzeRequest,
    GovernanceAnalysisResult,
    SecurityScoreResponse,
    ScoreBreakdownItem
)
from app.repository.agent_repository import get_agent_by_id, update_agent
from app.repository.credential_repository import get_latest_credential_by_agent_id

def compute_security_score(
    agent: Agent,
    credential: Optional[Credential] = None,
    failed_validations_count: int = 0
) -> Tuple[int, List[ScoreBreakdownItem]]:
    score = 100
    breakdown: List[ScoreBreakdownItem] = []
    now = datetime.now(timezone.utc)

    # 1. Credential status & age checks
    if not credential or not credential.active:
        penalty = 15
        score -= penalty
        breakdown.append(ScoreBreakdownItem(
            rule="NO_ACTIVE_CREDENTIAL",
            penalty=penalty,
            reason="Agent does not have an active credential."
        ))
    else:
        # Check credential age
        cred_created = credential.created_at
        if cred_created and cred_created.tzinfo is None:
            cred_created = cred_created.replace(tzinfo=timezone.utc)

        cred_age_days = (now - cred_created).days
        if cred_age_days > 90 and not credential.rotated_at:
            penalty = 20
            score -= penalty
            breakdown.append(ScoreBreakdownItem(
                rule="CREDENTIAL_AGE_OVER_90_DAYS",
                penalty=penalty,
                reason=f"Active credential age is {cred_age_days} days (exceeds 90-day threshold without rotation)."
            ))

    # 2. Scope tightness check
    allowed_scopes = agent.allowed_scopes or []
    if len(allowed_scopes) > 2:
        excess_count = len(allowed_scopes) - 2
        penalty = min(30, excess_count * 10)
        score -= penalty
        breakdown.append(ScoreBreakdownItem(
            rule="EXCESSIVE_SCOPES",
            penalty=penalty,
            reason=f"Agent has {len(allowed_scopes)} granted scopes (excess {excess_count} over 2-scope baseline)."
        ))

    # 3. Governance review flag
    if agent.flagged_for_review:
        penalty = 10
        score -= penalty
        breakdown.append(ScoreBreakdownItem(
            rule="FLAGGED_FOR_REVIEW",
            penalty=penalty,
            reason="Agent is flagged for security governance review due to inactivity or policy alert."
        ))

    # 4. Failed validation attempts penalty
    if failed_validations_count > 5:
        penalty = 15
        score -= penalty
        breakdown.append(ScoreBreakdownItem(
            rule="REPEATED_VALIDATION_FAILURES",
            penalty=penalty,
            reason=f"Agent encountered {failed_validations_count} failed credential validation attempts in recent history."
        ))

    final_score = max(0, min(100, score))
    return final_score, breakdown

def get_agent_security_score_service(db: Session, agent_id: str) -> SecurityScoreResponse:
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")

    cred = get_latest_credential_by_agent_id(db, agent_id)
    score, breakdown = compute_security_score(agent, cred)

    # Persist updated score on agent record
    if agent.security_score != score:
        update_agent(db, agent, {"security_score": score})

    return SecurityScoreResponse(
        agent_id=agent.id,
        security_score=score,
        risk_level=agent.risk_level,
        breakdown=breakdown
    )

def analyze_agent_governance_service(db: Session, payload: GovernanceAnalyzeRequest) -> GovernanceAnalysisResult:
    agent = get_agent_by_id(db, payload.agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{payload.agent_id}' not found.")

    cred = get_latest_credential_by_agent_id(db, payload.agent_id)
    score, breakdown = compute_security_score(agent, cred)

    issues: List[str] = [item.reason for item in breakdown]
    recommendations: List[str] = []

    for item in breakdown:
        if item.rule == "CREDENTIAL_AGE_OVER_90_DAYS":
            recommendations.append("Rotate agent credential immediately via POST /credentials/rotate.")
        elif item.rule == "NO_ACTIVE_CREDENTIAL":
            recommendations.append("Generate a new scoped credential via POST /credentials/generate.")
        elif item.rule == "EXCESSIVE_SCOPES":
            recommendations.append("Review allowed scopes and remove unneeded permissions (Principle of Least Privilege).")
        elif item.rule == "FLAGGED_FOR_REVIEW":
            recommendations.append("Perform governance review to verify if agent is still actively required.")
        elif item.rule == "REPEATED_VALIDATION_FAILURES":
            recommendations.append("Investigate credential validation failure logs for potential unauthorized invocation attempts.")

    if not recommendations:
        recommendations.append("Agent security posture is optimal. No action required.")

    # Update security score
    update_agent(db, agent, {"security_score": score})

    return GovernanceAnalysisResult(
        agent_id=agent.id,
        agent_name=agent.agent_name,
        security_score=score,
        risk_level=agent.risk_level,
        issues_detected=issues,
        recommendations=recommendations,
        analyzed_at=datetime.now(timezone.utc)
    )
