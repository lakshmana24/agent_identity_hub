import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduler.jobs import (
    check_expired_credentials_job,
    detect_stale_agents_job,
    generate_governance_reviews_job
)

logger = logging.getLogger("aih.scheduler")

scheduler = BackgroundScheduler()

def start_scheduler():
    logger.info("Starting APScheduler background task manager...")
    # Add recurring jobs
    scheduler.add_job(check_expired_credentials_job, "interval", hours=1, id="check_expired_credentials")
    scheduler.add_job(detect_stale_agents_job, "interval", hours=24, id="detect_stale_agents")
    scheduler.add_job(generate_governance_reviews_job, "cron", hour=0, minute=0, id="generate_governance_reviews")

    scheduler.start()
    logger.info("APScheduler started successfully.")

def shutdown_scheduler():
    if scheduler.running:
        logger.info("Shutting down APScheduler...")
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down cleanly.")
