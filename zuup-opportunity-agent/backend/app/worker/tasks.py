"""
Celery Tasks — Core async job handlers.
"""
import asyncio
from datetime import datetime, timezone

import boto3
import structlog

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import StudentProfile
from app.services.embedding_service import (
    build_profile_embedding_text, generate_embedding,
)
from app.services.resume_parser import parse_resume
from app.worker.celery_app import celery_app

logger = structlog.get_logger()


# ── Resume Parse Task ─────────────────────────────────────────

@celery_app.task(
    name="app.worker.tasks.parse_resume_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def parse_resume_task(self, job_id: str, user_id: str, s3_key: str, content_type: str):
    """
    1. Download resume from S3
    2. Parse with Claude LLM
    3. Update student profile in DB
    4. Trigger embedding generation
    """
    log = logger.bind(job_id=job_id, user_id=user_id)
    log.info("resume_parse.started")

    try:
        # Retrieve file bytes (from S3 or local fallback)
        if s3_key.startswith("local://"):
            import os
            relative_path = s3_key[len("local://"):]
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            local_path = os.path.join(base_dir, "storage", relative_path)
            with open(local_path, "rb") as f:
                file_bytes = f.read()
        else:
            # Download from S3
            s3 = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            response = s3.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
            file_bytes = response["Body"].read()

        # Parse resume (mock fallback logic is handled inside parse_resume function)
        parsed = asyncio.run(parse_resume(file_bytes, content_type))
        log.info("resume_parse.llm_complete")

        # Update profile in DB
        db = SessionLocal()
        try:
            from uuid import UUID
            profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == UUID(user_id)
            ).first()

            if not profile:
                log.error("resume_parse.profile_not_found")
                return {"status": "failed", "error": "Profile not found"}

            # Apply parsed fields (only if not null)
            if parsed.get("name"):
                profile.name = parsed["name"]
            if parsed.get("location"):
                profile.location = parsed["location"]
            if parsed.get("nationality"):
                profile.nationality = parsed["nationality"]
            if parsed.get("citizenship"):
                profile.citizenship = parsed["citizenship"]
            if parsed.get("skills"):
                profile.skills = parsed["skills"]
            if parsed.get("languages"):
                profile.languages = parsed["languages"]
            if parsed.get("interests"):
                profile.interests = parsed["interests"]

            # Education
            from app.models.models import Education
            if parsed.get("education"):
                db.query(Education).filter(Education.profile_id == profile.id).delete()
                for edu in parsed["education"]:
                    db.add(Education(
                        profile_id=profile.id,
                        institution=edu.get("institution", ""),
                        degree=edu.get("degree"),
                        field=edu.get("field"),
                        gpa=edu.get("gpa"),
                        gpa_scale=edu.get("gpa_scale", 4.0),
                        start_year=edu.get("start_year"),
                        end_year=edu.get("end_year"),
                        is_current=edu.get("is_current", False),
                    ))

            # Experience
            from app.models.models import Experience, ExperienceType
            if parsed.get("experience"):
                db.query(Experience).filter(Experience.profile_id == profile.id).delete()
                for exp in parsed["experience"]:
                    exp_type = exp.get("type", "work")
                    db.add(Experience(
                        profile_id=profile.id,
                        title=exp.get("title", ""),
                        org=exp.get("org", ""),
                        duration=exp.get("duration"),
                        type=ExperienceType(exp_type) if exp_type in ["work", "volunteer", "research"] else ExperienceType.WORK,
                    ))

            profile.resume_parsed_at = datetime.now(timezone.utc)

            # Recompute completeness
            from app.api.profile import compute_completeness
            profile.completeness_score = compute_completeness(profile)

            db.commit()
            profile_id = str(profile.id)
            log.info("resume_parse.db_updated", profile_id=profile_id)

        finally:
            db.close()

        # Trigger embedding generation
        generate_profile_embedding_task.delay(profile_id)

        return {"status": "done", "profile_id": profile_id}

    except Exception as exc:
        log.error("resume_parse.failed", error=str(exc))
        raise self.retry(exc=exc)


# ── Embedding Generation Task ─────────────────────────────────

@celery_app.task(
    name="app.worker.tasks.generate_profile_embedding_task",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def generate_profile_embedding_task(self, profile_id: str):
    """Generate and store embedding for a student profile."""
    log = logger.bind(profile_id=profile_id)
    try:
        db = SessionLocal()
        try:
            from uuid import UUID
            profile = db.query(StudentProfile).filter(
                StudentProfile.id == UUID(profile_id)
            ).first()
            if not profile:
                return

            profile_data = {
                "field_of_study": profile.field_of_study,
                "skills": profile.skills or [],
                "interests": profile.interests or [],
                "career_goals": profile.career_goals,
                "career_goal_tags": profile.career_goal_tags or [],
                "languages": profile.languages or [],
                "education": [
                    {"field": e.field, "institution": e.institution}
                    for e in (profile.education or [])
                ],
            }

            text = build_profile_embedding_text(profile_data)
            embedding = asyncio.run(generate_embedding(text))

            profile.embedding = embedding
            profile.embedding_updated_at = datetime.now(timezone.utc)
            db.commit()
            log.info("profile_embedding.generated")

        finally:
            db.close()

        # Trigger re-matching
        from app.worker.agent_tasks import run_matching_for_student_task
        run_matching_for_student_task.delay(profile_id)

    except Exception as exc:
        log.error("profile_embedding.failed", error=str(exc))
        raise self.retry(exc=exc)
