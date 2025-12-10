from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.notification import NotificationResponse
from src.services.notification_service import NotificationService
from src.api.dependencies import get_current_active_user, require_roles

router = APIRouter(prefix="/api/notifications", tags=["Хабарламалар"])

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    notifications = await NotificationService.get_user_notifications(
        db, current_user.user_id, unread_only
    )
    return notifications

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    notification = await NotificationService.get_notification_by_id(
        db, notification_id, current_user.user_id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хабарлама табылмады"
        )
    return notification

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    success = await NotificationService.mark_as_read(
        db, notification_id, current_user.user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хабарлама табылмады"
        )
    return {"message": "Хабарлама оқылған деп белгіленді"}

@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    await NotificationService.mark_all_as_read(db, current_user.user_id)
    return {"message": "Барлық хабарламалар оқылған деп белгіленді"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    success = await NotificationService.delete_notification(
        db, notification_id, current_user.user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хабарлама табылмады"
        )
    return {"message": "Хабарлама сәтті жойылды"}

@router.post("/send")
async def send_notification(
    user_id: int,
    message: str,
    notification_type: str = "system",
    channel: str = "email",
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "librarian"]))
):
    try:
        notification = await NotificationService.send_notification(
            db, user_id, notification_type, message, channel
        )
        return notification
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )