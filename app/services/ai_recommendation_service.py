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
    # Filter out deprecated scopes if any
    available_scopes = [s for s in scopes_manifest if not getattr(s, 'deprecated', False)]
    ai_client = get_ai_client()
    return ai_client.recommend_scopes(
        purpose=payload.purpose,
        available_scopes=available_scopes,
        model_provider=payload.model_provider or "Other",
        model_name=payload.model_name or "unknown",
        tools=payload.tools or []
    )

def generate_identity_summary_service(payload: IdentitySummaryRequest) -> IdentitySummaryResponse:
    ai_client = get_ai_client()
    summary = ai_client.generate_identity_summary(payload.model_dump())
    return IdentitySummaryResponse(summary=summary)
