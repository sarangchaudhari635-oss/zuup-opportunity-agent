"""
Matching Engine — 3-stage pipeline: Hard Filters → Semantic Scoring → Rank & Deduplicate.
Implements the PRD FR-003 specification.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    Application, Eligibility, Match,
    Opportunity, StudentProfile,
)
from app.services.embedding_service import cosine_similarity


# ─────────────────────────────────────────────────────────────
# STAGE 1 — Hard Filters
# ─────────────────────────────────────────────────────────────

def passes_hard_filters(
    profile: StudentProfile,
    opportunity: Opportunity,
    eligibility: Eligibility | None,
) -> bool:
    """
    Boolean gate — eliminate ineligible opportunities before scoring.
    Returns True if the student is eligible.
    """
    now = datetime.now(timezone.utc)

    # Exclude expired opportunities (deadline < 48h from now)
    if opportunity.deadline:
        min_deadline = now + timedelta(hours=48)
        if opportunity.deadline < min_deadline:
            return False

    if eligibility is None:
        return True  # No eligibility constraints = open to all

    # Nationality check
    if eligibility.nationality and profile.nationality:
        normalized_nat = profile.nationality.lower()
        eligible_nats = [n.lower() for n in eligibility.nationality]
        if eligible_nats and normalized_nat not in eligible_nats:
            return False

    # Citizenship check
    if eligibility.citizenship_required and profile.citizenship:
        required = set(c.lower() for c in eligibility.citizenship_required)
        has_citizenship = set(c.lower() for c in (profile.citizenship or []))
        if required and not required.intersection(has_citizenship):
            return False

    # GPA minimum
    if eligibility.gpa_min is not None and profile.gpa is not None:
        # Normalize GPA to the opportunity's scale
        profile_gpa = profile.gpa
        if profile.gpa_scale and eligibility.gpa_scale and profile.gpa_scale != eligibility.gpa_scale:
            profile_gpa = profile_gpa * (eligibility.gpa_scale / profile.gpa_scale)
        if profile_gpa < eligibility.gpa_min:
            return False

    # Enrollment status
    if eligibility.enrollment_status and profile.enrollment_status:
        eligible_statuses = [s.lower() for s in eligibility.enrollment_status]
        if eligible_statuses and profile.enrollment_status.lower() not in eligible_statuses:
            return False

    # Field of study (open if empty)
    if eligibility.field_of_study and profile.field_of_study:
        eligible_fields = [f.lower() for f in eligibility.field_of_study]
        student_field = profile.field_of_study.lower()
        # Partial match: "computer" matches "computer science"
        if eligible_fields and not any(f in student_field or student_field in f for f in eligible_fields):
            return False

    return True


# ─────────────────────────────────────────────────────────────
# STAGE 2 — Semantic Scoring
# ─────────────────────────────────────────────────────────────

def compute_semantic_score(
    profile: StudentProfile,
    opportunity: Opportunity,
) -> tuple[float, dict]:
    """
    Compute the full match score for a student-opportunity pair.
    Returns (final_score, breakdown_dict).
    """
    breakdown = {
        "semantic_score": 0.0,
        "skill_bonus": 0.0,
        "recency_bonus": 0.0,
        "location_bonus": 0.0,
    }

    # Semantic similarity (cosine)
    if profile.embedding and opportunity.embedding:
        cos_sim = cosine_similarity(profile.embedding, opportunity.embedding)
        semantic = round(cos_sim * 100, 2)  # Normalize 0–1 → 0–100
    else:
        semantic = 0.0
    breakdown["semantic_score"] = semantic

    # Skill overlap bonus (+5 per exact match, max +20)
    skill_bonus = 0.0
    if profile.skills and opportunity.description:
        opp_desc_lower = opportunity.description.lower()
        matched_skills = sum(
            1 for skill in profile.skills
            if skill.lower() in opp_desc_lower
        )
        skill_bonus = min(
            matched_skills * settings.skill_match_bonus,
            settings.skill_match_max_bonus,
        )
    breakdown["skill_bonus"] = skill_bonus

    # Recency bonus (+10 if posted within last 48h)
    recency_bonus = 0.0
    if opportunity.created_at:
        age_hours = (datetime.now(timezone.utc) - opportunity.created_at).total_seconds() / 3600
        if age_hours <= settings.recency_bonus_hours:
            recency_bonus = float(settings.recency_bonus_points)
    breakdown["recency_bonus"] = recency_bonus

    # Location bonus (+5 if location matches)
    location_bonus = 0.0
    if profile.location and opportunity.location:
        profile_country = profile.location.lower()
        opp_location = opportunity.location.lower()
        if profile_country in opp_location or opp_location in profile_country:
            location_bonus = float(settings.location_match_bonus)
    # Remote opportunities get location bonus if student has any location set
    if opportunity.remote_eligible and profile.location:
        location_bonus = max(location_bonus, float(settings.location_match_bonus))
    breakdown["location_bonus"] = location_bonus

    # Final score (capped at 100)
    final_score = min(
        semantic + skill_bonus + recency_bonus + location_bonus,
        100.0
    )

    return final_score, breakdown


# ─────────────────────────────────────────────────────────────
# STAGE 3 — Run Matching Pipeline
# ─────────────────────────────────────────────────────────────

def run_matching_for_student(db: Session, student_id: UUID) -> int:
    """
    Run the full matching pipeline for one student.
    Returns number of matches upserted.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile or not profile.embedding:
        return 0

    # Get all active, non-expired opportunities
    now = datetime.now(timezone.utc)
    min_deadline = now + timedelta(hours=48)
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.is_active == True)
        .filter(
            (Opportunity.deadline == None) | (Opportunity.deadline >= min_deadline)
        )
        .all()
    )

    # Get already-dismissed opportunities to skip
    dismissed_ids = set(
        m.opportunity_id for m in db.query(Match).filter(
            Match.student_id == student_id,
            Match.is_dismissed == True,
        ).all()
    )

    upserted = 0
    for opp in opportunities:
        if opp.id in dismissed_ids:
            continue

        # Stage 1: Hard filters
        if not passes_hard_filters(profile, opp, opp.eligibility):
            continue

        # Stage 2: Score
        score, breakdown = compute_semantic_score(profile, opp)

        # Skip very low scores
        if score < settings.min_match_score:
            continue

        # Stage 3: Upsert match record
        existing = db.query(Match).filter(
            Match.student_id == student_id,
            Match.opportunity_id == opp.id,
        ).first()

        if existing:
            existing.score = score
            existing.semantic_score = breakdown["semantic_score"]
            existing.skill_bonus = breakdown["skill_bonus"]
            existing.recency_bonus = breakdown["recency_bonus"]
            existing.location_bonus = breakdown["location_bonus"]
        else:
            match = Match(
                student_id=student_id,
                opportunity_id=opp.id,
                score=score,
                semantic_score=breakdown["semantic_score"],
                skill_bonus=breakdown["skill_bonus"],
                recency_bonus=breakdown["recency_bonus"],
                location_bonus=breakdown["location_bonus"],
            )
            db.add(match)

        upserted += 1

    db.commit()
    return upserted


def run_matching_for_opportunity(db: Session, opportunity_id: UUID) -> int:
    """
    Run matching when a new opportunity is ingested.
    Match it against all student profiles that have embeddings.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity or not opportunity.embedding:
        return 0

    profiles = db.query(StudentProfile).filter(StudentProfile.embedding != None).all()

    upserted = 0
    for profile in profiles:
        if not passes_hard_filters(profile, opportunity, opportunity.eligibility):
            continue

        score, breakdown = compute_semantic_score(profile, opportunity)
        if score < settings.min_match_score:
            continue

        existing = db.query(Match).filter(
            Match.student_id == profile.id,
            Match.opportunity_id == opportunity_id,
        ).first()

        if not existing:
            match = Match(
                student_id=profile.id,
                opportunity_id=opportunity_id,
                score=score,
                semantic_score=breakdown["semantic_score"],
                skill_bonus=breakdown["skill_bonus"],
                recency_bonus=breakdown["recency_bonus"],
                location_bonus=breakdown["location_bonus"],
            )
            db.add(match)
            upserted += 1

    db.commit()
    return upserted
