"""
Agent Tasks — Perceive→Reason→Act loop implementation.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog

from app.core.database import SessionLocal
from app.models.models import (
    Application, ApplicationStatus, Notification,
    NotificationSettings, NotificationType, Opportunity, StudentProfile, User,
)
from app.services.matching_engine import run_matching_for_student
from app.worker.celery_app import celery_app

logger = structlog.get_logger()


# ── REASON — Matching ─────────────────────────────────────────

@celery_app.task(name="app.worker.agent_tasks.run_matching_for_student_task")
def run_matching_for_student_task(profile_id: str):
    """Run full matching pipeline for one student."""
    db = SessionLocal()
    try:
        count = run_matching_for_student(db, UUID(profile_id))
        logger.info("matching.complete", profile_id=profile_id, matches=count)
    finally:
        db.close()


@celery_app.task(name="app.worker.agent_tasks.run_matching_all_students")
def run_matching_all_students():
    """Re-score all students — runs every 6 hours."""
    db = SessionLocal()
    try:
        profiles = db.query(StudentProfile).filter(StudentProfile.embedding != None).all()
        logger.info("matching.batch_start", total_students=len(profiles))
        for profile in profiles:
            run_matching_for_student_task.delay(str(profile.id))
    finally:
        db.close()


# ── ACT — Deadline Alerts ─────────────────────────────────────

REMINDER_DAYS = [14, 7, 3, 1]
REMINDER_NOTIFICATION_TYPES = {
    14: NotificationType.DEADLINE_14D,
    7: NotificationType.DEADLINE_7D,
    3: NotificationType.DEADLINE_3D,
    1: NotificationType.DEADLINE_1D,
}


@celery_app.task(name="app.worker.agent_tasks.check_deadline_alerts")
def check_deadline_alerts():
    """
    Check all active applications for upcoming deadlines.
    Send alerts at 14, 7, 3, and 1 days before deadline.
    Suppress if already submitted/outcome.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        active_statuses = [ApplicationStatus.SAVED, ApplicationStatus.APPLIED, ApplicationStatus.UNDER_REVIEW]

        for days in REMINDER_DAYS:
            target_date = now + timedelta(days=days)
            window_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            window_end = target_date.replace(hour=23, minute=59, second=59)

            apps = (
                db.query(Application)
                .join(Opportunity, Application.opportunity_id == Opportunity.id)
                .filter(
                    Application.status.in_(active_statuses),
                    Opportunity.deadline >= window_start,
                    Opportunity.deadline <= window_end,
                )
                .all()
            )

            for app in apps:
                opp = db.query(Opportunity).filter(Opportunity.id == app.opportunity_id).first()
                if not opp:
                    continue

                notif_type = REMINDER_NOTIFICATION_TYPES[days]
                day_label = f"{days} day{'s' if days > 1 else ''}"

                # Create in-app notification
                notif = Notification(
                    user_id=app.user_id,
                    type=notif_type,
                    title=f"⏰ {day_label} left: {opp.title}",
                    message=f"Your application for '{opp.title}' at {opp.organization} is due in {day_label}.",
                    action_url=f"/tracker",
                    opportunity_id=opp.id,
                    application_id=app.id,
                )
                db.add(notif)

                # Queue email alert
                from app.worker.email_tasks import send_deadline_alert_email
                send_deadline_alert_email.delay(
                    user_id=str(app.user_id),
                    opportunity_id=str(opp.id),
                    days_remaining=days,
                )

        db.commit()
        logger.info("deadline_alerts.complete")
    finally:
        db.close()


# ── ACT — Weekly Digest ───────────────────────────────────────

@celery_app.task(name="app.worker.agent_tasks.send_weekly_digest")
def send_weekly_digest():
    """Send weekly top-5 opportunities digest to all users. Runs Monday 9AM UTC."""
    from app.worker.email_tasks import send_weekly_digest_email
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            settings_row = db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user.id
            ).first()
            if settings_row and not settings_row.email_weekly_digest:
                continue
            send_weekly_digest_email.delay(str(user.id))
        logger.info("weekly_digest.queued", total=len(users))
    finally:
        db.close()
