# app/api/v1/routes/status.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.notification import NotificationStatusUpdate, APIResponse
from app.services.notification_service import NotificationService
from app.middleware.auth import verify_service_token

router = APIRouter()


@router.post("/email/status", response_model=APIResponse)
async def update_email_status(
    status_update: NotificationStatusUpdate,
    service_auth: dict = Depends(verify_service_token)
):
    """
    Email Service calls this endpoint to update notification status
    
    Requires service-to-service authentication
    """
    service = NotificationService()
    result = await service.update_notification_status(status_update)
    
    return result


@router.post("/push/status", response_model=APIResponse)
async def update_push_status(
    status_update: NotificationStatusUpdate,
    service_auth: dict = Depends(verify_service_token)
):
    """
    Push Service calls this endpoint to update notification status
    
    Requires service-to-service authentication
    """
    service = NotificationService()
    result = await service.update_notification_status(status_update)
    
    return result
