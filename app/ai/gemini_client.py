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
    def recommend_scopes(self, purpose: str, available_scopes: List[str]) -> ScopeRecommendationResponse:
        pass

    @abstractmethod
    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        pass

class MockAIClient(AIClient):
    def recommend_scopes(self, purpose: str, available_scopes: List[str]) -> ScopeRecommendationResponse:
        return get_mock_scope_recommendation(purpose, available_scopes)

    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        return get_mock_identity_summary(agent_data)

class LiveGeminiClient(AIClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to mock client.")
            self.model = None

    def recommend_scopes(self, purpose: str, available_scopes: List[str]) -> ScopeRecommendationResponse:
        if not self.model:
            return get_mock_scope_recommendation(purpose, available_scopes)

        prompt = f"""You are a security governance assistant for an enterprise AI agent identity platform.
Given the agent's stated business purpose, recommend the MINIMUM set of API scopes needed (principle of least privilege), and explicitly list scopes that should be REJECTED as excessive for this purpose.

Available scopes: {available_scopes}

Agent purpose: "{purpose}"

Respond with ONLY valid JSON, no markdown formatting, no preamble, matching exactly this schema:
{{
  "recommended_scopes": ["scope_name", ...],
  "rejected_scopes": ["scope_name", ...],
  "risk_level": "Low" | "Medium" | "High" | "Critical",
  "reasoning": "2-3 sentence explanation"
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Clean markdown JSON code fences if present
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
                reasoning=parsed.get("reasoning", "Recommended by Gemini AI governance assistant.")
            )
        except Exception as e:
            logger.error(f"Gemini live call failed: {e}. Falling back to mock heuristics.")
            return get_mock_scope_recommendation(purpose, available_scopes)

    def generate_identity_summary(self, agent_data: Dict[str, Any]) -> str:
        if not self.model:
            return get_mock_identity_summary(agent_data)

        prompt = f"""Write a concise, professional enterprise identity summary (3-4 sentences) for an AI agent with the following attributes, suitable for display on an internal governance dashboard. Do not invent facts not given below.

Agent name: {agent_data.get('agent_name')}
Purpose: {agent_data.get('purpose')}
Department: {agent_data.get('department')}
Granted scopes: {agent_data.get('scopes')}
Risk level: {agent_data.get('risk_level')}

Respond with plain text only, no markdown, no preamble.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini summary generation failed: {e}. Falling back to mock heuristics.")
            return get_mock_identity_summary(agent_data)

def get_ai_client() -> AIClient:
    if settings.AI_MODE.lower() == "live" and settings.GEMINI_API_KEY:
        return LiveGeminiClient(api_key=settings.GEMINI_API_KEY)
    return MockAIClient()
