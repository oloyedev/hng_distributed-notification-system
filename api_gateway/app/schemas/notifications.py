# app/schemas/notification.py
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4


class NotificationType(str, Enum):
    email = "email"
    push = "push"


class NotificationStatus(str, Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"


class UserData(BaseModel):
    name: str
    link: HttpUrl
    meta: Optional[Dict[str, Any]] = None


class NotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: UUID
    template_code: str
    variables: UserData
    request_id: str
    priority: int = Field(default=0, ge=0, le=10)
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    notification_id: str
    status: NotificationStatus
    created_at: datetime
    message: str


class NotificationStatusUpdate(BaseModel):
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None


class UserPreference(BaseModel):
    email: bool = True
    push: bool = True


class UserInfo(BaseModel):
    user_id: UUID
    name: str
    email: EmailStr
    push_token: Optional[str] = None
    preferences: UserPreference


class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: str
    meta: Optional[PaginationMeta] = None


class QueueMessage(BaseModel):
    """Message format for queue"""
    notification_id: str
    notification_type: NotificationType
    user_id: UUID
    recipient: str  # email or push_token
    template_code: str
    variables: Dict[str, Any]
    request_id: str
    priority: int
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
