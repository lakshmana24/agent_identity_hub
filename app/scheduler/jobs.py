import logging
from datetime import datetime, timezone
from app.database.session import SessionLocal
from app.models.credential import Credential
from app.models.agent import Agent
from app.models.audit_log import AuditLog
from app.repository.review_repository import find_stale_agents, create_review_report
from app.services.governance_service import compute_security_score

logger = logging.getLogger("aih.scheduler")

def check_expired_credentials_job():
    logger.info("Executing scheduled job: check_expired_credentials and check_agent_expirations")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # 1. Sweep expired credentials
        active_creds = db.query(Credential).filter(Credential.active == True).all()
        expired_cred_count = 0
        for cred in active_creds:
            exp = cred.expires_at
            if exp and exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)

            if exp < now:
                cred.active = False
                expired_cred_count += 1
                db.add(AuditLog(
                    action="credential.auto_expire",
                    method="SYSTEM",
                    path="/scheduler/check_expired_credentials",
                    agent_id=cred.agent_id,
                    performed_by="system_scheduler",
                    status_code=200,
                    status="success",
                    metadata_json={"credential_id": cred.id, "reason": "Expired past valid date"},
                    timestamp=now
                ))

        # 2. Sweep expired agent identities
        active_agents = db.query(Agent).filter(Agent.lifecycle_status == "active").all()
        decommissioned_agent_count = 0
        for agent in active_agents:
            ag_exp = agent.expiry_date
            if ag_exp and ag_exp.tzinfo is None:
                ag_exp = ag_exp.replace(tzinfo=timezone.utc)

            if ag_exp and ag_exp < now:
                agent.lifecycle_status = "decommissioned"
                decommissioned_agent_count += 1
                # Deactivate all credentials for this agent
                for c in db.query(Credential).filter(Credential.agent_id == agent.id, Credential.active == True).all():
                    c.active = False

                db.add(AuditLog(
                    action="agent.auto_decommission",
                    method="SYSTEM",
                    path="/scheduler/check_agent_expirations",
                    agent_id=agent.id,
                    performed_by="system_scheduler",
                    status_code=200,
                    status="success",
                    metadata_json={"reason": "Agent identity authorized lifetime expired"},
                    timestamp=now
                ))

        db.commit()
        logger.info(f"Sweeper job completed. Deactivated {expired_cred_count} credentials, decommissioned {decommissioned_agent_count} agents.")
    except Exception as e:
        logger.error(f"Error in check_expired_credentials_job: {e}")
    finally:
        db.close()

def detect_stale_agents_job():
    logger.info("Executing scheduled job: detect_stale_agents (30-day inactivity threshold)")
    db = SessionLocal()
    try:
        stale_agents = find_stale_agents(db, inactivity_days=30)
        logger.info(f"detect_stale_agents job completed. Identified {len(stale_agents)} stale agents.")
    except Exception as e:
        logger.error(f"Error in detect_stale_agents_job: {e}")
    finally:
        db.close()

def generate_governance_reviews_job():
    logger.info("Executing scheduled job: generate_governance_reviews")
    db = SessionLocal()
    try:
        active_agents = db.query(Agent).filter(Agent.lifecycle_status == "active").all()
        review_count = 0

        for agent in active_agents:
            cred = db.query(Credential).filter(Credential.agent_id == agent.id, Credential.active == True).first()
            score, breakdown = compute_security_score(agent, cred)

            if agent.flagged_for_review or (cred and (datetime.now(timezone.utc) - (cred.created_at.replace(tzinfo=timezone.utc) if cred.created_at.tzinfo is None else cred.created_at)).days > 90):
                rec = "review permissions"
                reasoning = "Agent credential age exceeds 90 days or agent has been flagged for inactivity review."
            elif score < 70:
                rec = "deprovision — inactive"
                reasoning = f"Low security score ({score}/100) due to multiple policy violations or excessive scopes."
            else:
                rec = "renew"
                reasoning = f"Optimal security posture with score {score}/100."

            create_review_report(db, {
                "agent_id": agent.id,
                "agent_name": agent.agent_name,
                "security_score": score,
                "recommendation": rec,
                "reasoning": reasoning
            })
            review_count += 1

        logger.info(f"generate_governance_reviews job completed. Generated {review_count} review reports.")
    except Exception as e:
        logger.error(f"Error in generate_governance_reviews_job: {e}")
    finally:
        db.close()
