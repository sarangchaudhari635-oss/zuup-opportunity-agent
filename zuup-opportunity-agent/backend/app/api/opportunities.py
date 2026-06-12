"""
Opportunity Feed API — paginated, filtered, scored feed.
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import CACHE_TTL, cache_get, cache_set
from app.models.models import Match, Opportunity, StudentProfile, User
from app.schemas.schemas import (
    FundingType, OpportunityCardResponse, OpportunityDetailResponse,
    OpportunityFeedResponse, OpportunityFilters, OpportunityType,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=OpportunityFeedResponse)
async def get_opportunity_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    type: list[OpportunityType] | None = Query(default=None),
    remote_only: bool = Query(default=False),
    min_score: int | None = Query(default=None, ge=0, le=100),
    funding_type: list[FundingType] | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the personalized opportunity feed for the authenticated student.
    Returns opportunities sorted by match score descending.
    """
    # Try cache first
    cache_key = f"opportunity_feed:{current_user.id}:{page}:{type}:{remote_only}:{min_score}:{q}"
    cached = await cache_get(cache_key)
    if cached:
        return OpportunityFeedResponse(**json.loads(cached))

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()

    # Build query — join matches for score
    query = (
        db.query(Opportunity, Match.score)
        .outerjoin(
            Match,
            (Match.opportunity_id == Opportunity.id)
            & (Match.student_id == (profile.id if profile else None))
            & (Match.is_dismissed == False),
        )
        .filter(Opportunity.is_active == True)
    )

    # Apply filters
    if type:
        query = query.filter(Opportunity.type.in_(type))
    if remote_only:
        query = query.filter(Opportunity.remote_eligible == True)
    if funding_type:
        query = query.filter(Opportunity.funding_type.in_(funding_type))
    if min_score is not None:
        query = query.filter(Match.score >= min_score)
    if q:
        q_clean = f"%{q.lower()}%"
        query = query.filter(
            Opportunity.title.ilike(q_clean) | Opportunity.description.ilike(q_clean)
        )

    # Exclude past deadlines
    now = datetime.now(timezone.utc)
    query = query.filter(
        (Opportunity.deadline == None) | (Opportunity.deadline >= now)
    )

    # Sort by match score descending, then by deadline ascending
    query = query.order_by(Match.score.desc().nullslast(), Opportunity.deadline.asc().nullslast())

    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for opp, score in results:
        card = OpportunityCardResponse(
            id=opp.id,
            title=opp.title,
            type=opp.type,
            organization=opp.organization,
            description_short=opp.description_short,
            deadline=opp.deadline,
            funding_type=opp.funding_type,
            location=opp.location,
            remote_eligible=opp.remote_eligible,
            url=opp.url,
            source_name=opp.source_name,
            match_score=round(score, 1) if score else None,
            created_at=opp.created_at,
        )
        items.append(card)

    response = OpportunityFeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )

    # Cache result
    await cache_set(cache_key, response.model_dump_json(), CACHE_TTL["opportunity_feed"])

    return response


@router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
async def get_opportunity_detail(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full detail for a single opportunity."""
    cache_key = f"opportunity:{opportunity_id}"
    cached = await cache_get(cache_key)
    if cached:
        return OpportunityDetailResponse(**json.loads(cached))

    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.is_active == True,
    ).first()

    if not opp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    # Get match score for this user
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    score = None
    if profile:
        match = db.query(Match).filter(
            Match.student_id == profile.id,
            Match.opportunity_id == opp.id,
        ).first()
        score = round(match.score, 1) if match else None

    from app.schemas.schemas import EligibilitySchema
    elig = None
    if opp.eligibility:
        elig = EligibilitySchema.model_validate(opp.eligibility)

    detail = OpportunityDetailResponse(
        id=opp.id, title=opp.title, type=opp.type, organization=opp.organization,
        description=opp.description, description_short=opp.description_short,
        deadline=opp.deadline, funding_type=opp.funding_type, funding_amount=opp.funding_amount,
        location=opp.location, remote_eligible=opp.remote_eligible, url=opp.url,
        source_name=opp.source_name, match_score=score, created_at=opp.created_at,
        eligibility=elig,
    )

    await cache_set(cache_key, detail.model_dump_json(), CACHE_TTL["opportunity_detail"])
    return detail
