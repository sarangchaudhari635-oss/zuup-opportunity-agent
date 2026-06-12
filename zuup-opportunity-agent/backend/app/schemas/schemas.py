"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.models import (
    ApplicationStatus, ExperienceType, FundingType,
    NotificationType, OpportunityType,
)


# ─────────────────────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ─────────────────────────────────────────────────────────────
# PROFILE SCHEMAS
# ─────────────────────────────────────────────────────────────

class EducationSchema(BaseModel):
    id: UUID | None = None
    institution: str
    degree: str | None = None
    field: str | None = None
    gpa: float | None = None
    gpa_scale: float = 4.0
    start_year: int | None = None
    end_year: int | None = None
    is_current: bool = False


class ExperienceSchema(BaseModel):
    id: UUID | None = None
    title: str
    org: str
    duration: str | None = None
    type: ExperienceType = ExperienceType.WORK
    description: str | None = None


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str | None
    location: str | None
    nationality: str | None
    citizenship: list[str]
    enrollment_status: str | None
    field_of_study: str | None
    skills: list[str]
    languages: list[str]
    interests: list[str]
    career_goals: str | None
    career_goal_tags: list[str]
    gpa: float | None
    completeness_score: int
    resume_parsed_at: datetime | None
    education: list[EducationSchema]
    experience: list[ExperienceSchema]
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    location: str | None = None
    nationality: str | None = None
    citizenship: list[str] | None = None
    enrollment_status: str | None = None
    field_of_study: str | None = None
    skills: list[str] | None = None
    languages: list[str] | None = None
    interests: list[str] | None = None
    career_goals: str | None = None
    career_goal_tags: list[str] | None = None
    gpa: float | None = None
    education: list[EducationSchema] | None = None
    experience: list[ExperienceSchema] | None = None


# ─────────────────────────────────────────────────────────────
# OPPORTUNITY SCHEMAS
# ─────────────────────────────────────────────────────────────

class EligibilitySchema(BaseModel):
    nationality: list[str] = []
    gpa_min: float | None = None
    enrollment_status: list[str] = []
    field_of_study: list[str] = []
    age_min: int | None = None
    age_max: int | None = None
    citizenship_required: list[str] = []
    raw_requirements: str | None = None

    class Config:
        from_attributes = True


class OpportunityCardResponse(BaseModel):
    """Lightweight response for feed cards."""
    id: UUID
    title: str
    type: OpportunityType
    organization: str
    description_short: str | None
    deadline: datetime | None
    funding_type: FundingType | None
    location: str | None
    remote_eligible: bool
    url: str
    source_name: str | None
    match_score: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class OpportunityDetailResponse(OpportunityCardResponse):
    """Full detail view."""
    description: str
    funding_amount: str | None
    eligibility: EligibilitySchema | None

    class Config:
        from_attributes = True


class OpportunityFeedResponse(BaseModel):
    items: list[OpportunityCardResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class OpportunityFilters(BaseModel):
    type: list[OpportunityType] | None = None
    deadline_min: datetime | None = None
    deadline_max: datetime | None = None
    remote_only: bool = False
    min_score: int | None = Field(default=None, ge=0, le=100)
    funding_type: list[FundingType] | None = None
    q: str | None = None


# ─────────────────────────────────────────────────────────────
# APPLICATION SCHEMAS
# ─────────────────────────────────────────────────────────────

class ApplicationCreateRequest(BaseModel):
    opportunity_id: UUID
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: str | None = None


class ApplicationUpdateRequest(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None
    requirements_checklist: list[dict] | None = None
    outcome_result: str | None = None


class ApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    opportunity: OpportunityCardResponse
    status: ApplicationStatus
    notes: str | None
    requirements_checklist: list[dict]
    applied_at: datetime | None
    outcome_at: datetime | None
    outcome_result: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# NOTIFICATION SCHEMAS
# ─────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    message: str
    action_url: str | None
    is_read: bool
    opportunity_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    email_weekly_digest: bool | None = None
    email_deadline_14d: bool | None = None
    email_deadline_7d: bool | None = None
    email_deadline_3d: bool | None = None
    email_deadline_1d: bool | None = None
    email_new_matches: bool | None = None
    inapp_new_matches: bool | None = None
    inapp_deadline_alerts: bool | None = None


# ─────────────────────────────────────────────────────────────
# RESUME SCHEMAS
# ─────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    job_id: str
    message: str
    status: str = "processing"


class ResumeParseStatus(BaseModel):
    job_id: str
    status: str   # pending | processing | done | failed
    profile_id: UUID | None = None
    error: str | None = None


# ─────────────────────────────────────────────────────────────
# COMMON
# ─────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
