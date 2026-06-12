"""
Celery App Configuration — Task queue for async jobs.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "zuup",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.worker.tasks",
        "app.worker.ingestion_tasks",
        "app.worker.agent_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
)

# ── Cron Schedule (Agent Loop) ────────────────────────────────

celery_app.conf.beat_schedule = {
    # PERCEIVE — Ingest new opportunities
    "ingest-hackathons": {
        "task": "app.worker.ingestion_tasks.ingest_all_hackathons",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
    },
    "ingest-scholarships": {
        "task": "app.worker.ingestion_tasks.ingest_all_scholarships",
        "schedule": crontab(minute=30, hour=2),  # Daily at 2:30 AM UTC
    },
    "ingest-fellowships": {
        "task": "app.worker.ingestion_tasks.ingest_all_fellowships",
        "schedule": crontab(minute=0, hour=3),   # Daily at 3 AM UTC
    },
    "ingest-internships": {
        "task": "app.worker.ingestion_tasks.ingest_all_internships",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "ingest-exchanges": {
        "task": "app.worker.ingestion_tasks.ingest_all_exchanges",
        "schedule": crontab(minute=0, hour=4, day_of_week=1),  # Weekly, Monday
    },

    # REASON — Re-score matches
    "run-matching-all-students": {
        "task": "app.worker.agent_tasks.run_matching_all_students",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },

    # ACT — Deadline alerts
    "check-deadline-alerts": {
        "task": "app.worker.agent_tasks.check_deadline_alerts",
        "schedule": crontab(minute=0, hour=8),  # Daily at 8 AM UTC
    },

    # ACT — Weekly digest (Monday 9 AM UTC)
    "send-weekly-digest": {
        "task": "app.worker.agent_tasks.send_weekly_digest",
        "schedule": crontab(minute=0, hour=9, day_of_week=1),
    },
}
