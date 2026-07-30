import json
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.ai.gemini_client import get_ai_client, LiveGeminiClient
from app.repository.agent_repository import get_agents, get_agent_by_id
from app.repository.review_repository import find_stale_agents, generate_team_quarterly_report
from app.repository.audit_repository import get_audit_logs

logger = logging.getLogger("aih.chatbot")

AIH_DOMAIN_KEYWORDS = [
    "agent", "credential", "scope", "team", "stale", "review",
    "audit", "log", "security", "score", "risk", "identity",
    "department", "active", "expired", "revoked", "decommissioned"
]

MUTATING_KEYWORDS = ["revoke", "delete", "remove", "create", "register", "rotate", "update", "modify"]

def _is_aih_domain_question(question: str) -> bool:
    q_lower = question.lower()
    return any(k in q_lower for k in AIH_DOMAIN_KEYWORDS)

def _is_mutating_request(question: str) -> bool:
    q_lower = question.lower()
    return any(k in q_lower for k in MUTATING_KEYWORDS)

def ask_chatbot_service(db: Session, question: str) -> str:
    # 1. Enforce read-only constraint
    if _is_mutating_request(question):
        return (
            "I am a read-only governance AI assistant. I cannot perform mutating actions "
            "(such as registering agents, rotating credentials, or revoking access). "
            "Please use the Agent Identity Hub dashboard UI or direct API endpoints to perform this operation."
        )

    # 2. Enforce strict AIH domain boundary
    if not _is_aih_domain_question(question):
        return "I can only answer questions about agents and data within Agent Identity Hub."

    # 3. Gather real context from AIH database
    try:
        agents, total_agents = get_agents(db, page=1, page_size=50)
        stale_list = find_stale_agents(db, inactivity_days=30)
        report_data = generate_team_quarterly_report(db)
        audit_logs, total_logs = get_audit_logs(db, page=1, page_size=10)

        context_summary = {
            "total_agents": total_agents,
            "active_agents_list": [
                {
                    "id": a.id,
                    "name": a.agent_name,
                    "owning_team": getattr(a, "owning_team", "Growth"),
                    "status": a.lifecycle_status,
                    "scopes": a.allowed_scopes,
                    "risk_level": a.risk_level,
                    "security_score": a.security_score
                }
                for a in agents
            ],
            "stale_agents_count": len(stale_list),
            "stale_agents": stale_list,
            "teams_quarterly_report": report_data.get("teams_reports", []),
            "recent_audit_count": total_logs
        }
    except Exception as e:
        logger.error(f"Failed to gather AIH context for chatbot: {e}")
        context_summary = {}

    ai_client = get_ai_client()

    if isinstance(ai_client, LiveGeminiClient) and ai_client.model:
        prompt = f"""You are the Agent Identity Hub (AIH) Enterprise Governance AI Assistant.

User Question: "{question}"

Current Live System Context from Database:
{json.dumps(context_summary, indent=2, default=str)}

Instructions:
1. Answer the user's question concisely using ONLY the provided AIH system context above.
2. If the user asks about agents, teams, staleness, credentials, or audit logs, synthesize exact figures from the context.
3. If the question cannot be answered from the provided AIH context or falls outside AIH governance domain, reply with: "I can only answer questions about agents and data within Agent Identity Hub."
4. Do NOT attempt to perform actions or fabricate data.

Answer in clear, professional natural language markdown:
"""
        try:
            res = ai_client.model.generate_content(prompt)
            return res.text.strip()
        except Exception as e:
            logger.error(f"Gemini chatbot generation failed: {e}. Falling back to rule-based responder.")

    # 4. Fallback mock natural language router
    q_lower = question.lower()
    if "stale" in q_lower or "30" in q_lower or "inactive" in q_lower:
        stale_cnt = len(context_summary.get("stale_agents", []))
        if stale_cnt == 0:
            return "There are currently **0 stale agents** detected. All active agents have executed API calls within the last 30 days."
        names = ", ".join([f"**{a['agent_name']}** ({a['owning_team']})" for a in context_summary.get("stale_agents", [])])
        return f"Identified **{stale_cnt} stale agent(s)** inactive for 30+ days: {names}. Review reports are available under `/reviews/report`."

    if "team" in q_lower or "growth" in q_lower or "report" in q_lower:
        teams = context_summary.get("teams_quarterly_report", [])
        if not teams:
            return f"Agent Identity Hub currently manages **{context_summary.get('total_agents', 0)} agents** across active teams."
        summary_lines = [f"- Team **{t['owning_team']}**: {t['total_active_agents']} active agents ({t['stale_count']} stale)" for t in teams]
        return f"### Team Quarterly Summary\n" + "\n".join(summary_lines)

    if "how many" in q_lower or "total" in q_lower or "agents" in q_lower:
        return f"Agent Identity Hub currently tracks **{context_summary.get('total_agents', 0)} registered agent identities** in the system directory."

    return (
        f"Agent Identity Hub is currently managing **{context_summary.get('total_agents', 0)} agents** and tracking "
        f"**{context_summary.get('stale_agents_count', 0)} stale agent(s)**. You can query specific details about agent scopes, "
        f"owning teams, quarterly review reports, or audit activity."
    )
