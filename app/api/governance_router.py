from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_admin
from app.config.settings import settings
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
from app.ai.gemini_client import get_ai_client, MockAIClient
from app.ai.groq_client import LiveGroqClient
from app.models.admin import Admin

router = APIRouter(prefix="/governance", tags=["Governance & Security Enforcement"])

@router.get("/ai-status")
def get_ai_status():
    mode = settings.AI_MODE.lower()
    has_groq = bool(settings.GROQ_API_KEY)
    has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "replace_with_your_gemini_api_key")
    ai_client = get_ai_client()
    is_mock = isinstance(ai_client, MockAIClient)

    live_ping = None
    if hasattr(ai_client, "test_live_connection"):
        live_ping = ai_client.test_live_connection()

    provider_name = "mock"
    if isinstance(ai_client, LiveGroqClient):
        provider_name = "groq"
    elif not is_mock:
        provider_name = "gemini"

    return {
        "ai_mode": "mock" if is_mock else "live",
        "provider": provider_name,
        "configured_ai_mode": mode,
        "groq_api_key_configured": has_groq,
        "gemini_api_key_configured": has_gemini,
        "live_ping": live_ping
    }

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
