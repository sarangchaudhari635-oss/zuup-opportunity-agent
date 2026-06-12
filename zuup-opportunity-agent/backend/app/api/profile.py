"""
Profile API — CRUD for student profiles with completeness scoring.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import cache_delete_pattern
from app.models.models import Education, Experience, StudentProfile, User
from app.schemas.schemas import (
    MessageResponse, ProfileResponse, ProfileUpdateRequest,
)
from app.worker.tasks import generate_profile_embedding_task

router = APIRouter(prefix="/profile", tags=["profile"])

COMPLETENESS_WEIGHTS = {
    "name": 10,
    "education": 20,
    "skills": 20,
    "experience": 15,
    "interests": 10,
    "location": 10,
    "career_goals": 15,
}


def compute_completeness(profile: StudentProfile) -> int:
    score = 0
    if profile.name:
        score += COMPLETENESS_WEIGHTS["name"]
    if profile.education:
        score += COMPLETENESS_WEIGHTS["education"]
    if profile.skills and len(profile.skills) >= 3:
        score += COMPLETENESS_WEIGHTS["skills"]
    if profile.experience:
        score += COMPLETENESS_WEIGHTS["experience"]
    if profile.interests:
        score += COMPLETENESS_WEIGHTS["interests"]
    if profile.location:
        score += COMPLETENESS_WEIGHTS["location"]
    if profile.career_goals:
        score += COMPLETENESS_WEIGHTS["career_goals"]
    return min(score, 100)


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.education), joinedload(StudentProfile.experience))
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.education), joinedload(StudentProfile.experience))
        .filter(StudentProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # Update scalar fields
    scalar_fields = [
        "name", "location", "nationality", "citizenship", "enrollment_status",
        "field_of_study", "skills", "languages", "interests", "career_goals",
        "career_goal_tags", "gpa",
    ]
    for field in scalar_fields:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(profile, field, value)

    # Update education (replace all)
    if payload.education is not None:
        db.query(Education).filter(Education.profile_id == profile.id).delete()
        for edu_data in payload.education:
            edu = Education(
                profile_id=profile.id,
                institution=edu_data.institution,
                degree=edu_data.degree,
                field=edu_data.field,
                gpa=edu_data.gpa,
                gpa_scale=edu_data.gpa_scale,
                start_year=edu_data.start_year,
                end_year=edu_data.end_year,
                is_current=edu_data.is_current,
            )
            db.add(edu)

    # Update experience (replace all)
    if payload.experience is not None:
        db.query(Experience).filter(Experience.profile_id == profile.id).delete()
        for exp_data in payload.experience:
            exp = Experience(
                profile_id=profile.id,
                title=exp_data.title,
                org=exp_data.org,
                duration=exp_data.duration,
                type=exp_data.type,
                description=exp_data.description,
            )
            db.add(exp)

    # Recompute completeness
    profile.completeness_score = compute_completeness(profile)

    db.commit()
    db.refresh(profile)

    # Invalidate cache and re-generate embedding async
    await cache_delete_pattern(f"opportunity_feed:{current_user.id}:*")
    generate_profile_embedding_task.delay(str(profile.id))

    return profile


@router.get("/me/completeness")
def get_completeness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    score = compute_completeness(profile)
    missing = []
    if not profile.name:
        missing.append({"field": "name", "label": "Full name", "points": 10})
    if not profile.education:
        missing.append({"field": "education", "label": "Education history", "points": 20})
    if not profile.skills or len(profile.skills) < 3:
        missing.append({"field": "skills", "label": "At least 3 skills", "points": 20})
    if not profile.experience:
        missing.append({"field": "experience", "label": "Work or volunteer experience", "points": 15})
    if not profile.interests:
        missing.append({"field": "interests", "label": "Interests", "points": 10})
    if not profile.location:
        missing.append({"field": "location", "label": "Location", "points": 10})
    if not profile.career_goals:
        missing.append({"field": "career_goals", "label": "Career goals", "points": 15})
    return {"score": score, "missing_fields": missing}
