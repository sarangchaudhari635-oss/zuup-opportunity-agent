"""
Application Tracker API — Kanban-style application management.
"""
import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Application, ApplicationStatus, Opportunity, User
from app.schemas.schemas import (
    ApplicationCreateRequest, ApplicationResponse,
    ApplicationUpdateRequest, MessageResponse,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save an opportunity to the application tracker."""
    # Check opportunity exists
    opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    # Check not already tracked
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.opportunity_id == payload.opportunity_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Opportunity already in your tracker.")

    app = Application(
        user_id=current_user.id,
        opportunity_id=payload.opportunity_id,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_response(app, opp)


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all tracked applications, optionally filtered by status."""
    query = (
        db.query(Application)
        .options(joinedload(Application.opportunity))
        .filter(Application.user_id == current_user.id)
        .order_by(Application.updated_at.desc())
    )
    if status_filter:
        query = query.filter(Application.status == status_filter)

    apps = query.all()
    return [_to_response(a, a.opportunity) for a in apps]


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update status, notes, or checklist for an application."""
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if payload.status is not None:
        app.status = payload.status
        from datetime import datetime, timezone
        if payload.status == ApplicationStatus.APPLIED:
            app.applied_at = datetime.now(timezone.utc)
        elif payload.status == ApplicationStatus.OUTCOME and payload.outcome_result:
            app.outcome_at = datetime.now(timezone.utc)

    if payload.notes is not None:
        app.notes = payload.notes
    if payload.requirements_checklist is not None:
        app.requirements_checklist = payload.requirements_checklist
    if payload.outcome_result is not None:
        app.outcome_result = payload.outcome_result

    db.commit()
    db.refresh(app)

    opp = db.query(Opportunity).filter(Opportunity.id == app.opportunity_id).first()
    return _to_response(app, opp)


@router.delete("/{application_id}", response_model=MessageResponse)
def delete_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an opportunity from the tracker."""
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    db.delete(app)
    db.commit()
    return MessageResponse(message="Application removed from tracker.")


@router.get("/export/csv")
def export_applications_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export all applications as CSV."""
    apps = (
        db.query(Application)
        .options(joinedload(Application.opportunity))
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "Title", "Organization", "Type", "Status", "Deadline",
        "Applied At", "Notes", "URL"
    ])
    writer.writeheader()

    for app in apps:
        opp = app.opportunity
        writer.writerow({
            "Title": opp.title if opp else "",
            "Organization": opp.organization if opp else "",
            "Type": opp.type.value if opp else "",
            "Status": app.status.value,
            "Deadline": opp.deadline.strftime("%Y-%m-%d") if opp and opp.deadline else "",
            "Applied At": app.applied_at.strftime("%Y-%m-%d") if app.applied_at else "",
            "Notes": app.notes or "",
            "URL": opp.url if opp else "",
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=zuup_applications.csv"},
    )


def _to_response(app: Application, opp: Opportunity) -> ApplicationResponse:
    from app.schemas.schemas import OpportunityCardResponse
    opp_card = OpportunityCardResponse(
        id=opp.id, title=opp.title, type=opp.type, organization=opp.organization,
        description_short=opp.description_short, deadline=opp.deadline,
        funding_type=opp.funding_type, location=opp.location,
        remote_eligible=opp.remote_eligible, url=opp.url,
        source_name=opp.source_name, match_score=None, created_at=opp.created_at,
    )
    return ApplicationResponse(
        id=app.id, user_id=app.user_id, opportunity_id=app.opportunity_id,
        opportunity=opp_card, status=app.status, notes=app.notes,
        requirements_checklist=app.requirements_checklist or [],
        applied_at=app.applied_at, outcome_at=app.outcome_at,
        outcome_result=app.outcome_result,
        created_at=app.created_at, updated_at=app.updated_at,
    )
