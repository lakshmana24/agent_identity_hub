from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin
from app.schemas.governance_schemas import (
    GovernanceAnalyzeRequest,
    GovernanceAnalysisResult,
    SecurityScoreResponse
)
from app.schemas.ai_schemas import (
    ScopeRecommendationRequest,
    ScopeRecommendationResponse,
    IdentitySummaryRequest,
    IdentitySummaryResponse
)
from app.services.governance_service import (
    analyze_agent_governance_service,
    get_agent_security_score_service
)
from app.services.ai_recommendation_service import (
    recommend_scopes_service,
    generate_identity_summary_service
)
from app.models.admin import Admin

router = APIRouter(prefix="/governance", tags=["Governance & Security Enforcement"])

@router.post("/analyze", response_model=GovernanceAnalysisResult)
def analyze_governance(
    payload: GovernanceAnalyzeRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return analyze_agent_governance_service(db, payload)

@router.get("/security-score/{agent_id}", response_model=SecurityScoreResponse)
def get_security_score(
    agent_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return get_agent_security_score_service(db, agent_id)

@router.post("/scope-recommendation", response_model=ScopeRecommendationResponse)
def recommend_scopes(
    payload: ScopeRecommendationRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return recommend_scopes_service(db, payload)

@router.post("/identity-summary", response_model=IdentitySummaryResponse)
def generate_identity_summary(
    payload: IdentitySummaryRequest,
    current_admin: Admin = Depends(get_current_admin)
):
    return generate_identity_summary_service(payload)
