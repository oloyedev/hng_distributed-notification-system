from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationType(str, Enum):
    email = "email"
    push = "push"


class NotificationStatus(str, Enum):
    delivered = "delivered"
    pending = "pending"
    failed = "failed"


class NotificationPriority(int, Enum):
    low = 1
    medium = 2
    high = 3
    critical = 4


class UserData(BaseModel):
    name: str
    link: Optional[HttpUrl] = None
    meta: Optional[Dict[str, Any]] = None


class PushNotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: str
    template_code: str
    variables: UserData
    request_id: str
    priority: int = Field(default=2, ge=1, le=4)
    metadata: Optional[Dict[str, Any]] = None


class PushMessage(BaseModel):
    title: str
    body: str
    image_url: Optional[str] = None
    click_action: Optional[str] = None
    data: Optional[Dict[str, str]] = None


class PushNotificationStatus(BaseModel):
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    checks: Dict[str, Any]


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: str
    meta: Optional[Dict[str, Any]] = None