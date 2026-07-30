from typing import List, Dict, Any
from app.schemas.ai_schemas import ScopeRecommendationResponse

def get_mock_scope_recommendation(purpose: str, available_scopes: List[str]) -> ScopeRecommendationResponse:
    p_lower = purpose.lower()

    if any(k in p_lower for k in ["refund", "payment", "stripe", "money", "billing"]):
        return ScopeRecommendationResponse(
            recommended_scopes=["crm:read", "tickets:read", "payments:read"],
            rejected_scopes=["payments:write", "inventory:write"],
            risk_level="High",
            reasoning="Purpose involves handling financial transactions and customer payments. Granting read-only payment access is recommended; write operations present financial risk and require strict manual governance."
        )

    if any(k in p_lower for k in ["ticket", "support", "customer", "helpdesk", "chat"]):
        return ScopeRecommendationResponse(
            recommended_scopes=["tickets:read", "tickets:write", "crm:read"],
            rejected_scopes=["payments:write", "inventory:write"],
            risk_level="Medium",
            reasoning="Agent focuses on customer support and ticket resolution. Granting support ticket management and CRM read access satisfies minimum privilege requirements."
        )

    if any(k in p_lower for k in ["inventory", "stock", "warehouse", "supply", "order"]):
        return ScopeRecommendationResponse(
            recommended_scopes=["inventory:read", "inventory:write"],
            rejected_scopes=["payments:write"],
            risk_level="Medium",
            reasoning="Agent manages warehouse product stock levels and order adjustments. Inventory write permissions allowed for automated stock sync."
        )

    return ScopeRecommendationResponse(
        recommended_scopes=["crm:read"],
        rejected_scopes=["crm:write", "payments:write", "inventory:write"],
        risk_level="Low",
        reasoning="General business agent. Defaulting to minimal read-only CRM access under the principle of least privilege."
    )

def get_mock_identity_summary(agent_data: Dict[str, Any]) -> str:
    name = agent_data.get("agent_name", "AI Agent")
    dept = agent_data.get("department", "General")
    purpose = agent_data.get("purpose", "Automates internal business tasks")
    scopes = agent_data.get("scopes", [])
    risk = agent_data.get("risk_level", "Low")

    scope_str = ", ".join(scopes) if scopes else "no explicit scopes"
    return f"{name} is an enterprise AI agent operating within the {dept} department. Its primary business purpose is to {purpose}. The agent is provisioned with {scope_str}, operating under a {risk} security risk classification within organizational governance guidelines."
