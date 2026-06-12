"""
Email Service — SendGrid transactional emails.
Handles: deadline reminders, weekly digest, welcome email.
"""
import asyncio
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Match, Notification, NotificationType, Opportunity, StudentProfile, User
from app.worker.celery_app import celery_app

logger = structlog.get_logger()


def _send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send a transactional email via SendGrid."""
    if not settings.sendgrid_api_key:
        logger.warning("email.skipped", reason="SENDGRID_API_KEY not set")
        return False

    message = Mail(
        from_email=From(settings.from_email, settings.from_name),
        to_emails=To(to_email),
        subject=subject,
        html_content=html_content,
    )
    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        sg.send(message)
        return True
    except Exception as e:
        logger.error("email.send_failed", error=str(e), to=to_email)
        return False


def _deadline_email_html(
    student_name: str,
    opportunity_title: str,
    organization: str,
    days_remaining: int,
    opportunity_url: str,
    tracker_url: str = "https://zuup.io/tracker",
) -> str:
    urgency_color = "#ef4444" if days_remaining <= 3 else "#f59e0b" if days_remaining <= 7 else "#8b5cf6"
    return f"""
    <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto; background: #0f1117; color: #f0f0f5; padding: 40px 32px; border-radius: 16px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <div style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #0ea5e9); width: 48px; height: 48px; border-radius: 12px; line-height: 48px; font-size: 24px; text-align: center;">🚀</div>
        <h1 style="color: #f0f0f5; font-size: 22px; margin: 12px 0 4px;">Zuup Opportunity Agent</h1>
      </div>

      <div style="background: #1a1f2e; border: 1px solid #2a3040; border-radius: 12px; padding: 28px; margin-bottom: 24px;">
        <div style="display: inline-block; background: {urgency_color}22; color: {urgency_color}; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; margin-bottom: 16px;">
          ⏰ {days_remaining} day{'s' if days_remaining > 1 else ''} remaining
        </div>
        <h2 style="color: #f0f0f5; font-size: 18px; margin: 0 0 8px;">{opportunity_title}</h2>
        <p style="color: #8892a4; font-size: 14px; margin: 0 0 20px;">{organization}</p>
        <a href="{opportunity_url}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #6d28d9); color: white; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px;">
          View & Apply →
        </a>
      </div>

      <p style="color: #8892a4; font-size: 13px; text-align: center;">
        Hi {student_name}, your Zuup agent flagged this deadline.<br>
        <a href="{tracker_url}" style="color: #8b5cf6;">View your tracker</a> · 
        <a href="https://zuup.io/settings/notifications" style="color: #8892a4;">Manage alerts</a>
      </p>
    </div>
    """


def _weekly_digest_html(student_name: str, opportunities: list[dict]) -> str:
    opp_cards = ""
    type_colors = {
        "scholarship": "#8b5cf6", "internship": "#0ea5e9",
        "fellowship": "#f59e0b", "hackathon": "#f97316", "exchange": "#3b82f6",
    }
    for opp in opportunities[:5]:
        color = type_colors.get(opp.get("type", ""), "#8b5cf6")
        deadline_str = opp.get("deadline_str", "No deadline")
        score = opp.get("score", 0)
        opp_cards += f"""
        <div style="background: #1a1f2e; border: 1px solid #2a3040; border-radius: 12px; padding: 20px; margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <span style="background: {color}22; color: {color}; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase;">{opp.get('type', '')}</span>
            <span style="color: {color}; font-size: 13px; font-weight: 700;">{score:.0f}% match</span>
          </div>
          <h3 style="color: #f0f0f5; font-size: 15px; margin: 0 0 4px;">{opp.get('title', '')}</h3>
          <p style="color: #8892a4; font-size: 13px; margin: 0 0 12px;">{opp.get('organization', '')} · {deadline_str}</p>
          <a href="{opp.get('url', '#')}" style="color: #8b5cf6; font-size: 13px; font-weight: 600; text-decoration: none;">View opportunity →</a>
        </div>
        """

    return f"""
    <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto; background: #0f1117; color: #f0f0f5; padding: 40px 32px; border-radius: 16px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <div style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #0ea5e9); width: 48px; height: 48px; border-radius: 12px; line-height: 48px; font-size: 24px; text-align: center;">🚀</div>
        <h1 style="color: #f0f0f5; font-size: 22px; margin: 12px 0 4px;">Your Weekly Digest</h1>
        <p style="color: #8892a4; font-size: 14px; margin: 0;">Top opportunities discovered for you this week</p>
      </div>
      {opp_cards}
      <div style="text-align: center; margin-top: 24px;">
        <a href="https://zuup.io/dashboard" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #6d28d9); color: white; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: 600;">
          See All Opportunities →
        </a>
      </div>
      <p style="color: #8892a4; font-size: 12px; text-align: center; margin-top: 24px;">
        Hi {student_name} — your agent is always working.<br>
        <a href="https://zuup.io/settings/notifications" style="color: #8892a4;">Unsubscribe from digest</a>
      </p>
    </div>
    """


# ── Celery Email Tasks ────────────────────────────────────────

@celery_app.task(name="app.worker.email_tasks.send_deadline_alert_email")
def send_deadline_alert_email(user_id: str, opportunity_id: str, days_remaining: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        opp = db.query(Opportunity).filter(Opportunity.id == UUID(opportunity_id)).first()
        if not user or not opp:
            return

        # Check user notification settings
        from app.models.models import NotificationSettings
        ns = db.query(NotificationSettings).filter(
            NotificationSettings.user_id == user.id
        ).first()
        field_map = {14: "email_deadline_14d", 7: "email_deadline_7d",
                     3: "email_deadline_3d", 1: "email_deadline_1d"}
        if ns and not getattr(ns, field_map.get(days_remaining, "email_deadline_7d"), True):
            return

        profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == user.id
        ).first()
        name = profile.name if profile and profile.name else user.email.split("@")[0]

        subject = f"⏰ {days_remaining} day{'s' if days_remaining > 1 else ''} left: {opp.title}"
        html = _deadline_email_html(
            student_name=name,
            opportunity_title=opp.title,
            organization=opp.organization,
            days_remaining=days_remaining,
            opportunity_url=opp.url,
        )
        _send_email(user.email, subject, html)
        logger.info("email.deadline_sent", user_id=user_id, days=days_remaining)
    finally:
        db.close()


@celery_app.task(name="app.worker.email_tasks.send_weekly_digest_email")
def send_weekly_digest_email(user_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            return

        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if not profile or not profile.embedding:
            return  # Skip users without profiles

        name = profile.name if profile and profile.name else user.email.split("@")[0]

        # Get top 5 matches
        from app.models.models import Match
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        one_week_ago = now - timedelta(days=7)

        top_matches = (
            db.query(Match, Opportunity)
            .join(Opportunity, Match.opportunity_id == Opportunity.id)
            .filter(
                Match.student_id == profile.id,
                Opportunity.is_active == True,
                Opportunity.created_at >= one_week_ago,
            )
            .order_by(Match.score.desc())
            .limit(5)
            .all()
        )

        if not top_matches:
            return  # No new opportunities this week

        opp_data = []
        for match, opp in top_matches:
            deadline_str = (
                opp.deadline.strftime("Due %b %d") if opp.deadline else "Open deadline"
            )
            opp_data.append({
                "title": opp.title,
                "organization": opp.organization,
                "type": opp.type.value if opp.type else "",
                "score": match.score,
                "deadline_str": deadline_str,
                "url": opp.url,
            })

        count = len(opp_data)
        subject = f"🎯 {count} new opportunit{'y' if count == 1 else 'ies'} match your profile"
        html = _weekly_digest_html(name, opp_data)
        _send_email(user.email, subject, html)
        logger.info("email.weekly_digest_sent", user_id=user_id, count=count)
    finally:
        db.close()


@celery_app.task(name="app.worker.email_tasks.send_welcome_email")
def send_welcome_email(user_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            return
        html = f"""
        <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto; background: #0f1117; color: #f0f0f5; padding: 40px 32px; border-radius: 16px; text-align: center;">
          <div style="background: linear-gradient(135deg, #7c3aed, #0ea5e9); width: 64px; height: 64px; border-radius: 16px; line-height: 64px; font-size: 32px; margin: 0 auto 20px; display: inline-block;">🚀</div>
          <h1 style="color: #f0f0f5; font-size: 26px; margin-bottom: 12px;">Welcome to Zuup!</h1>
          <p style="color: #8892a4; font-size: 15px; margin-bottom: 28px;">Your AI agent is now running in the background, continuously finding opportunities that match your profile.</p>
          <a href="https://zuup.io/onboarding" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #6d28d9); color: white; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 15px;">
            Upload Your Resume →
          </a>
          <p style="color: #8892a4; font-size: 13px; margin-top: 28px;">Takes less than 30 seconds. We'll do the rest.</p>
        </div>
        """
        _send_email(user.email, "🚀 Welcome to Zuup — Your agent is ready", html)
    finally:
        db.close()
