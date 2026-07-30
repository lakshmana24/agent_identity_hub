from typing import List, Dict, Any
from app.schemas.ai_schemas import ScopeRecommendationResponse

def get_mock_scope_recommendation(
    purpose: str,
    available_scopes: List[Any],
    model_provider: str = "Other",
    model_name: str = "unknown",
    tools: List[str] = None
) -> ScopeRecommendationResponse:
    p_lower = purpose.lower()
    tools = tools or []
    tool_str = " ".join(tools).lower()

    # High / Critical risk triggers from tools or purpose
    if "code_execution" in tool_str or "admin" in p_lower:
        return ScopeRecommendationResponse(
            recommended_scopes=["tickets:read", "crm:read"],
            rejected_scopes=["payments:write", "inventory:write", "crm:write"],
            risk_level="Critical",
            reasoning=f"Agent combines '{model_provider} {model_name}' with high-privilege capability tools ({', '.join(tools)}). Purpose '{purpose}' requires strict isolation; write permissions are rejected."
        )

    if any(k in p_lower for k in ["refund", "payment", "stripe", "money", "billing"]) or "send_email" in tool_str:
        return ScopeRecommendationResponse(
            recommended_scopes=["crm:read", "tickets:read", "payments:read"],
            rejected_scopes=["payments:write", "inventory:write"],
            risk_level="High",
            reasoning=f"Agent '{model_provider} {model_name}' performs financial transactions ('{purpose}') using tools [{', '.join(tools) if tools else 'none'}]. Granting read-only payment access is recommended; write access presents financial risk."
        )

    if any(k in p_lower for k in ["ticket", "support", "customer", "helpdesk", "chat"]):
        return ScopeRecommendationResponse(
            recommended_scopes=["tickets:read", "tickets:write", "crm:read"],
            rejected_scopes=["payments:write", "inventory:write"],
            risk_level="Medium",
            reasoning=f"Agent focuses on customer support and ticket resolution ('{purpose}'). Granting support ticket access and CRM read access satisfies minimum privilege requirements."
        )

    if any(k in p_lower for k in ["inventory", "stock", "warehouse", "supply", "order", "log", "monitor"]):
        return ScopeRecommendationResponse(
            recommended_scopes=["inventory:read", "inventory:write"],
            rejected_scopes=["payments:write"],
            risk_level="Medium",
            reasoning=f"Agent manages product stock levels or monitors system metrics ('{purpose}'). Inventory write permissions allowed for automated stock sync."
        )

    return ScopeRecommendationResponse(
        recommended_scopes=["crm:read"],
        rejected_scopes=["crm:write", "payments:write", "inventory:write"],
        risk_level="Low",
        reasoning=f"General business agent ('{purpose}') using {model_provider} {model_name}. Defaulting to minimal read-only CRM access under the principle of least privilege."
    )

def get_mock_identity_summary(agent_data: Dict[str, Any]) -> str:
    name = agent_data.get("agent_name", "AI Agent")
    dept = agent_data.get("department", "General")
    purpose = agent_data.get("purpose", "Automates internal business tasks")
    scopes = agent_data.get("scopes", [])
    risk = agent_data.get("risk_level", "Low")
    provider = agent_data.get("model_provider", "Other")
    model = agent_data.get("model_name", "unknown")
    tools = agent_data.get("tools", [])

    scope_str = ", ".join(scopes) if scopes else "no explicit scopes"
    tool_str = f" equipped with capabilities [{', '.join(tools)}]" if tools else ""
    return f"{name} is an enterprise AI agent built on {provider} ({model}){tool_str}, operating within the {dept} department. Its primary business purpose is to {purpose}. The agent is provisioned with {scope_str}, operating under a {risk} security risk classification."
