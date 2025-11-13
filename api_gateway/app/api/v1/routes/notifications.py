# app/api/v1/routes/notification.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List

from app.schemas.notification import (
    NotificationRequest,
    NotificationResponse,
    APIResponse
)
from app.services.notification_service import NotificationService
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/notifications", response_model=APIResponse)
async def create_notification(
    request: Request,
    notification_req: NotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new notification request
    
    - Validates the request
    - Checks user preferences
    - Routes to appropriate queue
    - Returns notification ID immediately
    """
    service = NotificationService()
    
    # Get correlation ID from middleware
    correlation_id = getattr(request.state, "correlation_id", None)
    
    result = await service.create_notification(
        notification_req, 
        correlation_id=correlation_id
    )
    
    return result


@router.get("/notifications/{notification_id}", response_model=APIResponse)
async def get_notification_status(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of a specific notification
    """
    service = NotificationService()
    result = await service.get_notification_status(notification_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    
    return result


@router.get("/notifications", response_model=APIResponse)
async def get_user_notifications(
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all notifications for the authenticated user
    """
    service = NotificationService()
    result = await service.get_user_notifications(
        user_id=current_user["user_id"],
        page=page,
        limit=limit
    )
    
    return result
