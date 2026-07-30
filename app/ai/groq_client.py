import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

from app.config.settings import settings
from app.schemas.ai_schemas import ScopeRecommendationResponse
from app.ai.mock_responses import get_mock_scope_recommendation

logger = logging.getLogger("aih.groq")

GROQ_MODEL = "llama-3.3-70b-versatile"

class LiveGroqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            logger.info(f"Initialized LiveGroqClient successfully with model '{GROQ_MODEL}'.")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq client: {e}.")
            self.client = None

    def test_live_connection(self) -> Dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Groq client instance not initialized."}
        try:
            res = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": "Ping test. Respond with 'PONG'."}],
                max_tokens=10
            )
            reply = res.choices[0].message.content.strip()
            return {"status": "ok", "provider": "groq", "model": GROQ_MODEL, "response": reply}
        except Exception as e:
            return {"status": "error", "provider": "groq", "message": str(e)}

    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        return get_mock_identity_summary(agent_data)

    def recommend_scopes(
        self,
        purpose: str,
        available_scopes: List[Any],
        model_provider: str = "Other",
        model_name: str = "unknown",
        tools: List[str] = None
    ) -> ScopeRecommendationResponse:
        tools = tools or []
        if not self.client:
            return get_mock_scope_recommendation(purpose, available_scopes, model_provider, model_name, tools)

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

        prompt = f"""You are an IAM security governance expert analyzing an AI agent request.

Agent Technical Details:
- Purpose: "{purpose}"
- Tools: {tools}

Available Resource Scopes in IAM Manifest:
{scopes_formatted}

Task:
1. Select recommended_scopes required for stated purpose.
2. Select rejected_scopes that are excessive or high risk.
3. Classify overall risk_level as "Low", "Medium", "High", or "Critical".
4. Provide specific reasoning (1-2 sentences) explaining why this risk level was assigned based on granted scopes and purpose.

Respond strictly in raw JSON format:
{{
  "recommended_scopes": ["scope_name"],
  "rejected_scopes": ["scope_name"],
  "risk_level": "Low" | "Medium" | "High" | "Critical",
  "reasoning": "Agent has write access to payment records (payments:write), which can directly execute financial transactions."
}}
"""
        try:
            res = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            text = res.choices[0].message.content.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            parsed = json.loads(text)
            return ScopeRecommendationResponse(
                recommended_scopes=parsed.get("recommended_scopes", []),
                rejected_scopes=parsed.get("rejected_scopes", []),
                risk_level=parsed.get("risk_level", "Medium"),
                reasoning=parsed.get("reasoning", f"Assigned {parsed.get('risk_level', 'Medium')} risk based on requested tool permissions.")
            )
        except Exception as e:
            logger.error(f"Groq recommendation call failed: {e}. Falling back to mock heuristics.")
            return get_mock_scope_recommendation(purpose, available_scopes, model_provider, model_name, tools)
