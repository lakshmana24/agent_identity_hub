import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from app.config.settings import settings
from app.schemas.ai_schemas import ScopeRecommendationResponse
from app.ai.mock_responses import get_mock_scope_recommendation, get_mock_identity_summary

logger = logging.getLogger("aih.ai")

class AIClient(ABC):
    @abstractmethod
    def recommend_scopes(
        self,
        purpose: str,
        available_scopes: List[Any],
        model_provider: str = "Other",
        model_name: str = "unknown",
        tools: List[str] = None
    ) -> ScopeRecommendationResponse:
        pass

    @abstractmethod
    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        pass

class MockAIClient(AIClient):
    def recommend_scopes(
        self,
        purpose: str,
        available_scopes: List[Any],
        model_provider: str = "Other",
        model_name: str = "unknown",
        tools: List[str] = None
    ) -> ScopeRecommendationResponse:
        return get_mock_scope_recommendation(purpose, available_scopes, model_provider, model_name, tools)

    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        return get_mock_identity_summary(agent_data)

class LiveGeminiClient(AIClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Initialized LiveGeminiClient successfully with model gemini-1.5-flash.")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to mock client.")
            self.model = None

    def test_live_connection(self) -> Dict[str, Any]:
        if not self.model:
            return {"status": "error", "message": "Gemini model instance not initialized."}
        try:
            res = self.model.generate_content("Ping test. Respond with word 'PONG'.")
            return {"status": "ok", "response": res.text.strip()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def recommend_scopes(
        self,
        purpose: str,
        available_scopes: List[Any],
        model_provider: str = "Other",
        model_name: str = "unknown",
        tools: List[str] = None
    ) -> ScopeRecommendationResponse:
        tools = tools or []
        if not self.model:
            return get_mock_scope_recommendation(purpose, available_scopes, model_provider, model_name, tools)

        # Format scope details with descriptions if available
        scope_descriptions = []
        for s in available_scopes:
            if hasattr(s, "scope_name"):
                desc = getattr(s, "description", "") or s.scope_name
                scope_descriptions.append(f"- {s.scope_name}: {desc} (Risk: {getattr(s, 'risk_level', 'Medium')})")
            elif isinstance(s, dict):
                scope_descriptions.append(f"- {s.get('scope_name')}: {s.get('description', '')} (Risk: {s.get('risk_level', 'Medium')})")
            else:
                scope_descriptions.append(f"- {str(s)}")

        scopes_formatted = "\n".join(scope_descriptions)

        prompt = f"""You are an enterprise IAM security governance expert analyzing an AI agent identity request.

Agent Technical Profile:
- Model Provider: {model_provider}
- Model Name: {model_name}
- Capability Tools: {tools}
- Stated Purpose: "{purpose}"

Available Resource Scopes in IAM Manifest:
{scopes_formatted}

Task:
1. Select the MINIMAL set of recommended_scopes required to fulfill the stated purpose (Principle of Least Privilege).
2. Identify rejected_scopes that are excessive or pose unnecessary security risk for this agent's profile.
3. Classify overall risk_level as "Low", "Medium", "High", or "Critical". Note: agents with high-privilege tools (e.g. code_execution, email sending, payments) or frontier models MUST be rated at higher risk.
4. Write a reasoning string (2-3 sentences) explicitly QUOTING key terms from the stated purpose and tools to justify your security recommendation.

Respond with ONLY valid raw JSON, no markdown formatting (no ```json code blocks), matching exactly:
{{
  "recommended_scopes": ["scope_name", ...],
  "rejected_scopes": ["scope_name", ...],
  "risk_level": "Low" | "Medium" | "High" | "Critical",
  "reasoning": "Explicit reasoning quoting specific purpose and tool details..."
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            parsed = json.loads(text)
            logger.info(f"Gemini live scope recommendation succeeded for purpose '{purpose[:30]}...'")
            return ScopeRecommendationResponse(
                recommended_scopes=parsed.get("recommended_scopes", []),
                rejected_scopes=parsed.get("rejected_scopes", []),
                risk_level=parsed.get("risk_level", "Medium"),
                reasoning=parsed.get("reasoning", "Recommended by Gemini AI governance analysis.")
            )
        except Exception as e:
            logger.error(f"Gemini live recommendation call failed: {e}. Falling back to mock heuristics.")
            return get_mock_scope_recommendation(purpose, available_scopes, model_provider, model_name, tools)

    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        if not self.model:
            return get_mock_identity_summary(agent_data)

        prompt = f"""Write a concise, professional enterprise identity summary (3-4 sentences) for an AI agent with the following attributes:

Agent name: {agent_data.get('agent_name')}
Provider & Model: {agent_data.get('model_provider')} ({agent_data.get('model_name')})
Tools & Capabilities: {agent_data.get('tools')}
Purpose: {agent_data.get('purpose')}
Department: {agent_data.get('department')}
Granted API Scopes: {agent_data.get('scopes')}
Risk Level: {agent_data.get('risk_level')}

Respond with plain text only, no markdown formatting.
"""
        try:
            response = self.model.generate_content(prompt)
            logger.info("Gemini live identity summary succeeded.")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini live summary generation failed: {e}. Falling back to mock heuristics.")
            return get_mock_identity_summary(agent_data)

def get_ai_client() -> AIClient:
    if settings.AI_MODE.lower() == "live" and settings.GEMINI_API_KEY:
        return LiveGeminiClient(api_key=settings.GEMINI_API_KEY)
    return MockAIClient()
