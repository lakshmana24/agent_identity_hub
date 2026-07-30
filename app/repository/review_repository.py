from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.credential import Credential
from app.models.review_report import ReviewReport

def create_review_report(db: Session, report_data: dict) -> ReviewReport:
    report = ReviewReport(**report_data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_review_reports(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[ReviewReport], int]:
    query = db.query(ReviewReport)
    total = query.count()
    reports = query.order_by(ReviewReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return reports, total

def find_stale_agents(db: Session, inactivity_days: int = 30) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=inactivity_days)

    active_agents = db.query(Agent).filter(Agent.lifecycle_status == "active").all()
    stale_list: List[Dict[str, Any]] = []

    for agent in active_agents:
        # Check credential usage (last_used_at)
        cred = db.query(Credential).filter(Credential.agent_id == agent.id, Credential.active == True).first()

        last_activity = None
        if cred and cred.last_used_at:
            last_activity = cred.last_used_at
        else:
            last_activity = agent.created_at

        if last_activity and last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)

        days_inactive = (now - last_activity).days

        if last_activity <= threshold:
            if not agent.flagged_for_review:
                agent.flagged_for_review = True
                db.commit()

            stale_list.append({
                "agent_id": agent.id,
                "agent_name": agent.agent_name,
                "owning_team": getattr(agent, "owning_team", "Growth") or "Growth",
                "owner": agent.owner,
                "last_used_at": last_activity,
                "call_count": cred.call_count if cred else 0,
                "days_inactive": days_inactive,
                "flagged_for_review": agent.flagged_for_review
            })

    return stale_list

def generate_team_quarterly_report(db: Session, owning_team: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    threshold_30d = now - timedelta(days=30)

    query = db.query(Agent).filter(Agent.lifecycle_status == "active")
    if owning_team:
        query = query.filter(Agent.owning_team == owning_team)

    active_agents = query.all()

    # Group active agents by owning_team
    teams_dict: Dict[str, List[Agent]] = {}
    for agent in active_agents:
        team = getattr(agent, "owning_team", "Growth") or "Growth"
        teams_dict.setdefault(team, []).append(agent)

    team_reports = []

    for team, agents in teams_dict.items():
        stale_agents = []
        healthy_agents = []

        for agent in agents:
            cred = db.query(Credential).filter(Credential.agent_id == agent.id, Credential.active == True).first()
            last_activity = cred.last_used_at if cred and cred.last_used_at else agent.created_at
            if last_activity and last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

            days_inactive = (now - last_activity).days
            agent_summary = {
                "agent_id": agent.id,
                "agent_name": agent.agent_name,
                "owning_team": team,
                "last_used_at": last_activity,
                "call_count": cred.call_count if cred else 0,
                "days_inactive": days_inactive
            }

            if last_activity <= threshold_30d:
                stale_agents.append(agent_summary)
            else:
                healthy_agents.append(agent_summary)

        stale_cnt = len(stale_agents)
        total_cnt = len(agents)
        if stale_cnt == 0:
            rec_summary = f"All {total_cnt} active agents in team '{team}' are healthy and actively utilized."
        else:
            rec_summary = f"{stale_cnt} of {total_cnt} active agents in team '{team}' are stale (inactive 30+ days) and should be reviewed for decommissioning."

        team_reports.append({
            "owning_team": team,
            "total_active_agents": total_cnt,
            "stale_count": stale_cnt,
            "healthy_count": len(healthy_agents),
            "stale_agents": stale_agents,
            "healthy_agents": healthy_agents,
            "recommendation_summary": rec_summary
        })

    return {
        "generated_at": now,
        "filter_owning_team": owning_team,
        "total_teams_evaluated": len(team_reports),
        "teams_reports": team_reports
    }
