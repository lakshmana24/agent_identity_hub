from sqlalchemy.orm import Session
from app.schemas.ai_schemas import (
    ScopeRecommendationRequest,
    ScopeRecommendationResponse,
    IdentitySummaryRequest,
    IdentitySummaryResponse
)
from app.repository.agent_repository import get_all_scopes
from app.ai.gemini_client import get_ai_client

def recommend_scopes_service(db: Session, payload: ScopeRecommendationRequest) -> ScopeRecommendationResponse:
    scopes_manifest = get_all_scopes(db)
    available_scopes = [s.scope_name for s in scopes_manifest]
    ai_client = get_ai_client()
    return ai_client.recommend_scopes(purpose=payload.purpose, available_scopes=available_scopes)

def generate_identity_summary_service(payload: IdentitySummaryRequest) -> IdentitySummaryResponse:
    ai_client = get_ai_client()
    summary = ai_client.generate_identity_summary(payload.model_dump())
    return IdentitySummaryResponse(summary=summary)
