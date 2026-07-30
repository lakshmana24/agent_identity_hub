import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.ai.gemini_client import get_ai_client
from app.ai.groq_client import LiveGroqClient, GROQ_MODEL
from app.repository.agent_repository import get_agents, get_agent_by_id
from app.repository.review_repository import find_stale_agents, generate_team_quarterly_report
from app.repository.audit_repository import get_audit_logs
from app.services.dashboard_service import get_dashboard_service
from app.services.identity_service import build_identity_card

logger = logging.getLogger("aih.chatbot")

AIH_DOMAIN_KEYWORDS = [
    "agent", "credential", "scope", "team", "stale", "review",
    "audit", "log", "security", "score", "risk", "identity",
    "active", "expired", "revoked", "decommissioned", "dashboard",
    "metrics", "report", "growth", "finance", "devops", "logistics", "support"
]

MUTATING_KEYWORDS = ["revoke", "delete", "remove", "create", "register", "rotate", "update", "modify"]

def _is_aih_domain_question(question: str) -> bool:
    q_lower = question.lower()
    return any(k in q_lower for k in AIH_DOMAIN_KEYWORDS)

def _is_mutating_request(question: str) -> bool:
    q_lower = question.lower()
    return any(k in q_lower for k in MUTATING_KEYWORDS)

# --- Stage 1: Tool Execution Registry ---

CHATBOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_agents",
            "description": "Lists agents in the directory with optional filtering by status (active, suspended, decommissioned) or owning_team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: active, suspended, or decommissioned"},
                    "owning_team": {"type": "string", "description": "Filter by owning team: Growth, Finance, DevOps, Customer Support, Logistics"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_agent_detail",
            "description": "Gets full identity record for a specific agent by agent_id or exact name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string", "description": "Agent ID (e.g. agt_123) or agent_name"}
                },
                "required": ["identifier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_stale_agents",
            "description": "Lists active agents that have not executed API calls in 30+ days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inactivity_days": {"type": "integer", "description": "Threshold in days (default 30)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_review_report",
            "description": "Generates team quarterly access review report grouped by owning_team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owning_team": {"type": "string", "description": "Filter report to specific team name"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_audit_logs",
            "description": "Queries audit log trail with optional filtering by agent_id or action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Filter audit logs by agent_id"},
                    "action": {"type": "string", "description": "Filter by action name e.g. agent.register, credential.validate"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_metrics",
            "description": "Returns aggregate system metrics (total agents, active credentials, risk distribution, security score averages).",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def _execute_tool(db: Session, tool_name: str, tool_args: Dict[str, Any]) -> Any:
    logger.info(f"[Retriever Stage 1] Executing tool: {tool_name} with args: {tool_args}")
    try:
        if tool_name == "list_agents":
            agents, total = get_agents(
                db,
                status=tool_args.get("status"),
                owning_team=tool_args.get("owning_team"),
                page=1,
                page_size=50
            )
            result = [
                {
                    "agent_id": a.id,
                    "agent_name": a.agent_name,
                    "owning_team": getattr(a, "owning_team", "Growth"),
                    "status": a.lifecycle_status,
                    "scopes": a.allowed_scopes,
                    "risk_level": a.risk_level,
                    "risk_reasoning": a.risk_reasoning
                }
                for a in agents
            ]
            logger.info(f"[Retriever Stage 1] list_agents returned {len(result)} records (total: {total})")
            return {"total": total, "agents": result}

        elif tool_name == "get_agent_detail":
            identifier = tool_args.get("identifier", "")
            agent = get_agent_by_id(db, identifier)
            if not agent:
                # Fallback search by name
                all_a, _ = get_agents(db, page=1, page_size=100)
                matching = [a for a in all_a if a.agent_name.lower() == identifier.lower()]
                if matching:
                    agent = matching[0]

            if not agent:
                return {"error": f"Agent '{identifier}' not found."}

            card = build_identity_card(db, agent)
            logger.info(f"[Retriever Stage 1] get_agent_detail returned card for {agent.agent_name}")
            return card.model_dump()

        elif tool_name == "list_stale_agents":
            days = tool_args.get("inactivity_days", 30)
            stale_data = find_stale_agents(db, inactivity_days=days)
            logger.info(f"[Retriever Stage 1] list_stale_agents returned {len(stale_data)} stale agents")
            return stale_data

        elif tool_name == "get_review_report":
            team = tool_args.get("owning_team")
            report = generate_team_quarterly_report(db, owning_team=team)
            logger.info(f"[Retriever Stage 1] get_review_report returned report for team '{team}'")
            return report

        elif tool_name == "search_audit_logs":
            logs, total = get_audit_logs(
                db,
                agent_id=tool_args.get("agent_id"),
                action=tool_args.get("action"),
                page=1,
                page_size=20
            )
            result = [
                {
                    "action": l.action,
                    "agent_id": l.agent_id,
                    "performed_by": l.performed_by,
                    "status": l.status,
                    "timestamp": l.timestamp.isoformat() if l.timestamp else None
                }
                for l in logs
            ]
            logger.info(f"[Retriever Stage 1] search_audit_logs returned {len(result)} logs")
            return {"total": total, "logs": result}

        elif tool_name == "get_dashboard_metrics":
            metrics = get_dashboard_service(db).model_dump()
            logger.info(f"[Retriever Stage 1] get_dashboard_metrics returned summary")
            return metrics

        else:
            return {"error": f"Unknown tool name '{tool_name}'"}
    except Exception as e:
        logger.error(f"[Retriever Stage 1] Tool execution failed for {tool_name}: {e}")
        return {"error": str(e)}


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

    ai_client = get_ai_client()

    # Stage 1 & 2 via Groq if available
    if isinstance(ai_client, LiveGroqClient) and ai_client.client:
        try:
            # --- STAGE 1: RETRIEVER AGENT (TOOL CALLING) ---
            retriever_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are the Stage 1 Retriever Agent for Agent Identity Hub. "
                        "Determine which internal database tool(s) are needed to answer the user's question, "
                        "and invoke them using tool/function calls."
                    )
                },
                {"role": "user", "content": question}
            ]

            res1 = ai_client.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=retriever_messages,
                tools=CHATBOT_TOOLS,
                tool_choice="auto",
                temperature=0.0
            )

            msg1 = res1.choices[0].message
            retrieved_data = []

            if msg1.tool_calls:
                for tool_call in msg1.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments or "{}")
                    tool_output = _execute_tool(db, fn_name, fn_args)
                    retrieved_data.append({
                        "tool": fn_name,
                        "arguments": fn_args,
                        "data": tool_output
                    })
            else:
                # If model chose not to call a tool, infer best tool call from question
                q_lower = question.lower()
                if "stale" in q_lower:
                    data = _execute_tool(db, "list_stale_agents", {})
                    retrieved_data.append({"tool": "list_stale_agents", "arguments": {}, "data": data})
                elif "report" in q_lower:
                    data = _execute_tool(db, "get_review_report", {})
                    retrieved_data.append({"tool": "get_review_report", "arguments": {}, "data": data})
                elif "audit" in q_lower or "log" in q_lower:
                    data = _execute_tool(db, "search_audit_logs", {})
                    retrieved_data.append({"tool": "search_audit_logs", "arguments": {}, "data": data})
                else:
                    data = _execute_tool(db, "list_agents", {})
                    retrieved_data.append({"tool": "list_agents", "arguments": {}, "data": data})

            # --- STAGE 2: RESPONDER AGENT (NO TOOL ACCESS) ---
            responder_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are the Stage 2 Responder Agent for Agent Identity Hub.\n"
                        "Your job is to answer the user's question using ONLY the provided retrieved data from Stage 1.\n"
                        "Rules:\n"
                        "1. Only state facts present in the provided retrieved data. Reference real agent names, actual counts, and exact dates.\n"
                        "2. If the data is empty or shows no matching items, say so plainly (e.g., 'No agents are currently stale').\n"
                        "3. Never invent agent names, counts, dates, or metrics (such as uptime percentage) not present in the retrieved data.\n"
                        "4. Never attempt to take actions."
                    )
                },
                {
                    "role": "user",
                    "content": f"User Question: \"{question}\"\n\nRetrieved Structured Data from Stage 1:\n{json.dumps(retrieved_data, indent=2, default=str)}"
                }
            ]

            res2 = ai_client.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=responder_messages,
                temperature=0.2
            )
            return res2.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq two-stage chatbot execution failed: {e}. Falling back to deterministic retriever.")

    # --- FALLBACK DETERMINISTIC RETRIEVER + RESPONDER ---
    q_lower = question.lower()
    
    # Check for requested fields that don't exist (e.g. uptime percentage)
    if "uptime" in q_lower or "cpu" in q_lower or "latency" in q_lower:
        return f"Uptime and performance telemetry data is not tracked or available in Agent Identity Hub."

    if "stale" in q_lower:
        stale_data = _execute_tool(db, "list_stale_agents", {})
        if not stale_data:
            return "No agents are currently stale. All active agents have executed API calls within the last 30 days."
        items = [f"- **{a['agent_name']}** (ID: `{a['agent_id']}`, Team: {a['owning_team']}, Days Inactive: {a['days_inactive']})" for a in stale_data]
        return f"Identified **{len(stale_data)} stale agent(s)** inactive for 30+ days:\n" + "\n".join(items)

    if "scope" in q_lower or "permissions" in q_lower:
        # Search if specific agent mentioned
        all_agents_res = _execute_tool(db, "list_agents", {})
        agents = all_agents_res.get("agents", [])
        matched = [a for a in agents if a["agent_name"].lower() in q_lower or a["agent_id"].lower() in q_lower]
        if matched:
            a = matched[0]
            scopes_str = ", ".join([f"`{s}`" for s in a["scopes"]]) if a["scopes"] else "no scopes"
            return f"Agent **{a['agent_name']}** (Team: {a['owning_team']}) is granted tool scopes: {scopes_str}."

    if "report" in q_lower or "quarterly" in q_lower:
        report = _execute_tool(db, "get_review_report", {})
        teams = report.get("teams_reports", [])
        if not teams:
            return "No quarterly review report data is available."
        lines = [f"- Team **{t['owning_team']}**: {t['total_active_agents']} active agents ({t['stale_count']} stale, {t['healthy_count']} healthy). {t['recommendation_summary']}" for t in teams]
        return "### Team Quarterly Review Report\n" + "\n".join(lines)

    # Default active agents list
    agents_res = _execute_tool(db, "list_agents", {"status": "active"})
    active_list = agents_res.get("agents", [])
    if not active_list:
        return "There are currently 0 active agents registered in Agent Identity Hub."

    agent_lines = [f"- **{a['agent_name']}** (ID: `{a['agent_id']}`, Owning Team: **{a['owning_team']}**, Scopes: {', '.join(a['scopes'])})" for a in active_list]
    return f"### Currently Active Agents ({len(active_list)})\n" + "\n".join(agent_lines)
