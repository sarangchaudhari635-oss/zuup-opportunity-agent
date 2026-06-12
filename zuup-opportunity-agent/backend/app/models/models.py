"""
SQLAlchemy ORM Models for Zuup Opportunity Agent.
All tables defined here — imported by Alembic for migrations.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Enum, ARRAY, JSON,
    UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────

class OpportunityType(str, PyEnum):
    SCHOLARSHIP = "scholarship"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    HACKATHON = "hackathon"
    EXCHANGE = "exchange"


class FundingType(str, PyEnum):
    FULLY_FUNDED = "fully_funded"
    PARTIAL = "partial"
    UNPAID = "unpaid"
    STIPEND = "stipend"


class ExperienceType(str, PyEnum):
    WORK = "work"
    VOLUNTEER = "volunteer"
    RESEARCH = "research"


class ApplicationStatus(str, PyEnum):
    SAVED = "saved"
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    OUTCOME = "outcome"


class NotificationType(str, PyEnum):
    NEW_MATCH = "new_match"
    DEADLINE_14D = "deadline_14d"
    DEADLINE_7D = "deadline_7d"
    DEADLINE_3D = "deadline_3d"
    DEADLINE_1D = "deadline_1d"
    STATUS_UPDATE = "status_update"
    WEEKLY_DIGEST = "weekly_digest"
    PROFILE_PROMPT = "profile_prompt"


# ─────────────────────────────────────────────────────────────
# USER & AUTH
# ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Null for Google OAuth users
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    notification_settings = relationship(
        "NotificationSettings", back_populates="user", uselist=False
    )


# ─────────────────────────────────────────────────────────────
# STUDENT PROFILE
# ─────────────────────────────────────────────────────────────

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Identity
    name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)           # City, Country
    nationality = Column(String(100), nullable=True)
    citizenship = Column(ARRAY(String), default=list)        # Multiple citizenships

    # Status
    enrollment_status = Column(String(100), nullable=True)  # enrolled, graduated, etc.
    field_of_study = Column(String(255), nullable=True)

    # Arrays (stored as PostgreSQL ARRAY)
    skills = Column(ARRAY(String), default=list)
    languages = Column(ARRAY(String), default=list)
    interests = Column(ARRAY(String), default=list)

    # Goals
    career_goals = Column(Text, nullable=True)
    career_goal_tags = Column(ARRAY(String), default=list)  # Structured goal tags

    # GPA (optional)
    gpa = Column(Float, nullable=True)
    gpa_scale = Column(Float, default=4.0)

    # Resume
    resume_s3_key = Column(String(512), nullable=True)
    resume_parsed_at = Column(DateTime(timezone=True), nullable=True)
    resume_parse_confidence = Column(Float, nullable=True)

    # Completeness
    completeness_score = Column(Integer, default=0)         # 0–100

    # Embedding (pgvector) — 1536 dims for text-embedding-3-small
    embedding = Column(Vector(1536), nullable=True)
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Preference weights (feedback loop)
    preference_weights = Column(JSON, default=dict)          # keyword → weight

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
    education = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")


class Education(Base):
    __tablename__ = "education"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"))
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=True)
    field = Column(String(255), nullable=True)
    gpa = Column(Float, nullable=True)
    gpa_scale = Column(Float, default=4.0)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    is_current = Column(Boolean, default=False)

    profile = relationship("StudentProfile", back_populates="education")


class Experience(Base):
    __tablename__ = "experience"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    org = Column(String(255), nullable=False)
    duration = Column(String(100), nullable=True)           # e.g. "Jun 2023 – Aug 2023"
    type = Column(Enum(ExperienceType), default=ExperienceType.WORK)
    description = Column(Text, nullable=True)

    profile = relationship("StudentProfile", back_populates="experience")


# ─────────────────────────────────────────────────────────────
# OPPORTUNITIES
# ─────────────────────────────────────────────────────────────

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core fields
    title = Column(String(512), nullable=False)
    type = Column(Enum(OpportunityType), nullable=False, index=True)
    organization = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    description_short = Column(String(500), nullable=True)  # LLM-generated 50-word summary

    # Deadline & funding
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    funding_type = Column(Enum(FundingType), nullable=True)
    funding_amount = Column(String(255), nullable=True)     # e.g. "$5,000 stipend"

    # Location
    location = Column(String(255), nullable=True)
    remote_eligible = Column(Boolean, default=False)

    # Source
    url = Column(String(2048), nullable=False)
    source_name = Column(String(255), nullable=True)        # e.g. "devpost", "daad"
    source_id = Column(String(512), nullable=True)          # Source's own ID

    # Deduplication hash
    content_hash = Column(String(64), unique=True, nullable=True, index=True)  # SHA256

    # Embedding (pgvector)
    embedding = Column(Vector(1536), nullable=True)
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Quality
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    quality_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_seen_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    eligibility = relationship("Eligibility", back_populates="opportunity", uselist=False)
    matches = relationship("Match", back_populates="opportunity")

    __table_args__ = (
        Index("ix_opportunities_type_deadline", "type", "deadline"),
        Index("ix_opportunities_active_deadline", "is_active", "deadline"),
    )


class Eligibility(Base):
    __tablename__ = "eligibility"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True
    )

    nationality = Column(ARRAY(String), default=list)       # Empty = open to all
    gpa_min = Column(Float, nullable=True)
    gpa_scale = Column(Float, default=4.0)
    enrollment_status = Column(ARRAY(String), default=list) # enrolled, recent_grad, etc.
    field_of_study = Column(ARRAY(String), default=list)    # Empty = all fields
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    citizenship_required = Column(ARRAY(String), default=list)
    raw_requirements = Column(Text, nullable=True)          # Original requirements text

    opportunity = relationship("Opportunity", back_populates="eligibility")


# ─────────────────────────────────────────────────────────────
# MATCHING
# ─────────────────────────────────────────────────────────────

class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"))
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"))

    # Scores
    score = Column(Float, nullable=False)                   # 0–100 final score
    semantic_score = Column(Float, nullable=True)           # Raw cosine similarity
    skill_bonus = Column(Float, default=0)
    recency_bonus = Column(Float, default=0)
    location_bonus = Column(Float, default=0)

    # State
    is_seen = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    opportunity = relationship("Opportunity", back_populates="matches")

    __table_args__ = (
        UniqueConstraint("student_id", "opportunity_id", name="uq_match_student_opportunity"),
        Index("ix_matches_student_score", "student_id", "score"),
    )


# ─────────────────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"))

    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SAVED, index=True)
    notes = Column(Text, nullable=True)
    requirements_checklist = Column(JSON, default=list)     # [{item: str, done: bool}]

    applied_at = Column(DateTime(timezone=True), nullable=True)
    outcome_at = Column(DateTime(timezone=True), nullable=True)
    outcome_result = Column(String(50), nullable=True)      # accepted, rejected, waitlisted

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="applications")
    opportunity = relationship("Opportunity")

    __table_args__ = (
        UniqueConstraint("user_id", "opportunity_id", name="uq_application_user_opportunity"),
        Index("ix_applications_user_status", "user_id", "status"),
    )


# ─────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(2048), nullable=True)

    is_read = Column(Boolean, default=False, index=True)
    is_emailed = Column(Boolean, default=False)

    # Optional link to related entity
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    user = relationship("User", back_populates="notifications")


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Email preferences
    email_weekly_digest = Column(Boolean, default=True)
    email_deadline_14d = Column(Boolean, default=True)
    email_deadline_7d = Column(Boolean, default=True)
    email_deadline_3d = Column(Boolean, default=True)
    email_deadline_1d = Column(Boolean, default=True)
    email_new_matches = Column(Boolean, default=False)      # Weekly batch, not every match

    # In-app preferences
    inapp_new_matches = Column(Boolean, default=True)
    inapp_deadline_alerts = Column(Boolean, default=True)

    # Digest timing
    digest_day_of_week = Column(Integer, default=0)         # 0=Monday
    digest_hour_utc = Column(Integer, default=9)            # 9 AM

    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="notification_settings")
