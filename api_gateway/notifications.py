from fastapi import APIRouter, HTTPException
import uuid
from schemas import StandardResponse, EmailNotification, PushNotification
from utils import publish_message

router = APIRouter()

@router.post("/email", response_model=StandardResponse)
def send_email(notification: EmailNotification):
    request_id = str(uuid.uuid4())
    payload = notification.dict()
    payload["request_id"] = request_id
    try:
        publish_message("email.queue", payload)
    except HTTPException as e:
        return StandardResponse(success=False, message="Failed to enqueue email", error=str(e.detail))
    return StandardResponse(success=True, message="Email notification queued", data={"request_id": request_id})

@router.post("/push", response_model=StandardResponse)
def send_push(notification: PushNotification):
    request_id = str(uuid.uuid4())
    payload = notification.dict()
    payload["request_id"] = request_id
    try:
        publish_message("push.queue", payload)
    except HTTPException as e:
        return StandardResponse(success=False, message="Failed to enqueue push notification", error=str(e.detail))
    return StandardResponse(success=True, message="Push notification queued", data={"request_id": request_id})
