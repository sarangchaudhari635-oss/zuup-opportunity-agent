"""
Notifications API — in-app notification feed and settings.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Notification, NotificationSettings, User
from app.schemas.schemas import (
    MessageResponse, NotificationResponse, NotificationSettingsUpdate,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return in-app notifications for the current user."""
    query = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    if unread_only:
        query = query.filter(Notification.is_read == False)

    return query.limit(limit).all()


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=MessageResponse)
def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.is_read = True
    db.commit()
    return MessageResponse(message="Marked as read.")


@router.patch("/read-all", response_model=MessageResponse)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return MessageResponse(message="All notifications marked as read.")


@router.get("/settings")
def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings_row = db.query(NotificationSettings).filter(
        NotificationSettings.user_id == current_user.id
    ).first()
    if not settings_row:
        raise HTTPException(status_code=404, detail="Settings not found.")
    return settings_row


@router.patch("/settings", response_model=MessageResponse)
def update_notification_settings(
    payload: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings_row = db.query(NotificationSettings).filter(
        NotificationSettings.user_id == current_user.id
    ).first()
    if not settings_row:
        raise HTTPException(status_code=404, detail="Settings not found.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(settings_row, field, value)

    db.commit()
    return MessageResponse(message="Notification settings updated.")
