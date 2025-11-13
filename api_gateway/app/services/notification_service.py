# app/services/notification_service.py
import httpx
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Optional

from app.schemas.notification import (
    NotificationRequest,
    NotificationStatusUpdate,
    NotificationStatus,
    QueueMessage,
    PaginationMeta
)
from app.core.redis import redis_manager
from app.core.rabbitmq import rabbitmq_manager
from app.core.config import settings
from app.utils.logger import setup_logger
from app.services.circuit_breaker import CircuitBreaker

logger = setup_logger(__name__)


class NotificationService:
    def __init__(self):
        self.user_service_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            timeout=settings.CIRCUIT_BREAKER_TIMEOUT,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
    
    async def create_notification(
        self, 
        request: NotificationRequest,
        correlation_id: Optional[str] = None
    ) -> Dict:
        """
        Main method to create and queue notification
        
        Steps:
        1. Check idempotency
        2. Validate user preferences
        3. Enrich message
        4. Route to queue
        5. Store status
        6. Return response
        """
        try:
            # 1. Idempotency check
            existing = await self._check_idempotency(request.request_id)
            if existing:
                return {
                    "success": True,
                    "data": existing,
                    "message": "Notification already processed (idempotent)",
                    "error": None,
                    "meta": None
                }
            
            # 2. Get user preferences with circuit breaker
            user_info = await self._get_user_info(request.user_id)
            if not user_info:
                return {
                    "success": False,
                    "data": None,
                    "error": "User service unavailable or user not found",
                    "message": "Failed to retrieve user information",
                    "meta": None
                }
            
            # 3. Check if user allows this notification type
            if request.notification_type.value == "email" and not user_info.get("preferences", {}).get("email", True):
                return {
                    "success": False,
                    "data": None,
                    "error": "User has disabled email notifications",
                    "message": "Notification blocked by user preference",
                    "meta": None
                }
            
            if request.notification_type.value == "push" and not user_info.get("preferences", {}).get("push", True):
                return {
                    "success": False,
                    "data": None,
                    "error": "User has disabled push notifications",
                    "message": "Notification blocked by user preference",
                    "meta": None
                }
            
            # 4. Get recipient (email or push_token)
            recipient = self._get_recipient(user_info, request.notification_type.value)
            if not recipient:
                return {
                    "success": False,
                    "data": None,
                    "error": f"User has no {request.notification_type.value} configured",
                    "message": "Missing recipient information",
                    "meta": None
                }
            
            # 5. Generate notification ID
            notification_id = f"notif_{uuid4().hex}"
            
            # 6. Create queue message
            queue_message = QueueMessage(
                notification_id=notification_id,
                notification_type=request.notification_type,
                user_id=request.user_id,
                recipient=recipient,
                template_code=request.template_code,
                variables=request.variables.model_dump(),
                request_id=request.request_id,
                priority=request.priority,
                timestamp=datetime.utcnow(),
                retry_count=0,
                max_retries=settings.MAX_RETRIES,
                correlation_id=correlation_id,
                metadata=request.metadata
            )
            
            # 7. Publish to queue
            published = await rabbitmq_manager.publish_to_queue(
                notification_type=request.notification_type.value,
                message=queue_message.model_dump(mode='json'),
                priority=request.priority,
                correlation_id=correlation_id
            )
            
            if not published:
                return {
                    "success": False,
                    "data": None,
                    "error": "Failed to queue notification",
                    "message": "Message queue unavailable",
                    "meta": None
                }
            
            # 8. Store notification status
            await self._store_notification_status(notification_id, request, NotificationStatus.pending)
            
            # 9. Store idempotency key
            await self._store_idempotency(request.request_id, notification_id)
            
            # 10. Return response
            return {
                "success": True,
                "data": {
                    "notification_id": notification_id,
                    "status": NotificationStatus.pending.value,
                    "created_at": datetime.utcnow().isoformat()
                },
                "message": "Notification queued successfully",
                "error": None,
                "meta": None
            }
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": "Failed to create notification",
                "meta": None
            }
    
    async def _check_idempotency(self, request_id: str) -> Optional[Dict]:
        """Check if request was already processed"""
        key = f"request:{request_id}"
        notification_id = await redis_manager.get(key)
        
        if notification_id:
            # Get notification status
            status_data = await self._get_status_from_cache(notification_id)
            return status_data
        
        return None
    
    async def _store_idempotency(self, request_id: str, notification_id: str):
        """Store request ID for idempotency"""
        key = f"request:{request_id}"
        await redis_manager.set(key, notification_id, ttl=settings.IDEMPOTENCY_TTL_SECONDS)
    
    async def _get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Get user info from User Service with circuit breaker
        """
        # Check cache first
        cache_key = f"user:{user_id}"
        cached = await redis_manager.get_json(cache_key)
        if cached:
            logger.info(f"User info retrieved from cache: {user_id}")
            return cached
        
        # Call User Service with circuit breaker
        try:
            if not self.user_service_breaker.can_execute():
                logger.warning("User service circuit breaker is open")
                return None
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    user_info = data.get("data")
                    
                    # Cache for 5 minutes
                    await redis_manager.set_json(cache_key, user_info, ttl=300)
                    
                    self.user_service_breaker.record_success()
                    return user_info
                else:
                    self.user_service_breaker.record_failure()
                    logger.error(f"User service returned {response.status_code}")
                    return None
                    
        except Exception as e:
            self.user_service_breaker.record_failure()
            logger.error(f"Error calling user service: {e}")
            return None
    
    def _get_recipient(self, user_info: Dict, notification_type: str) -> Optional[str]:
        """Extract recipient from user info"""
        if notification_type == "email":
            return user_info.get("email")
        elif notification_type == "push":
            return user_info.get("push_token")
        return None
    
    async def _store_notification_status(
        self, 
        notification_id: str, 
        request: NotificationRequest,
        status: NotificationStatus
    ):
        """Store notification status in Redis"""
        key = f"notification:{notification_id}"
        data = {
            "notification_id": notification_id,
            "user_id": str(request.user_id),
            "notification_type": request.notification_type.value,
            "status": status.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "request_id": request.request_id
        }
        
        await redis_manager.set_json(key, data, ttl=settings.NOTIFICATION_TTL_SECONDS)
        
        # Also add to user's notification list
        user_key = f"user_notifications:{request.user_id}"
        await redis_manager.client.lpush(user_key, notification_id)
        await redis_manager.expire(user_key, settings.NOTIFICATION_TTL_SECONDS)
    
    async def update_notification_status(
        self, 
        status_update: NotificationStatusUpdate
    ) -> Dict:
        """Update notification status (called by Email/Push services)"""
        try:
            key = f"notification:{status_update.notification_id}"
            notification = await redis_manager.get_json(key)
            
            if not notification:
                return {
                    "success": False,
                    "data": None,
                    "error": "Notification not found",
                    "message": "Invalid notification ID",
                    "meta": None
                }
            
            # Update status
            notification["status"] = status_update.status.value
            notification["updated_at"] = (status_update.timestamp or datetime.utcnow()).isoformat()
            
            if status_update.error:
                notification["error"] = status_update.error
            
            await redis_manager.set_json(key, notification, ttl=settings.NOTIFICATION_TTL_SECONDS)
            
            logger.info(f"Notification {status_update.notification_id} status updated to {status_update.status}")
            
            return {
                "success": True,
                "data": notification,
                "message": "Status updated successfully",
                "error": None,
                "meta": None
            }
            
        except Exception as e:
            logger.error(f"Error updating notification status: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": "Failed to update status",
                "meta": None
            }
    
    async def get_notification_status(self, notification_id: str) -> Dict:
        """Get notification status"""
        status_data = await self._get_status_from_cache(notification_id)
        
        if not status_data:
            return {
                "success": False,
                "data": None,
                "error": "Notification not found",
                "message": "Invalid notification ID or expired",
                "meta": None
            }
        
        return {
            "success": True,
            "data": status_data,
            "message": "Notification found",
            "error": None,
            "meta": None
        }
    
    async def _get_status_from_cache(self, notification_id: str) -> Optional[Dict]:
        """Get notification status from cache"""
        key = f"notification:{notification_id}"
        return await redis_manager.get_json(key)
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        page: int = 1, 
        limit: int = 20
    ) -> Dict:
        """Get paginated notifications for a user"""
        try:
            user_key = f"user_notifications:{user_id}"
            
            # Get total count
            total = await redis_manager.client.llen(user_key)
            
            if total == 0:
                return {
                    "success": True,
                    "data": [],
                    "message": "No notifications found",
                    "error": None,
                    "meta": PaginationMeta(
                        total=0,
                        limit=limit,
                        page=page,
                        total_pages=0,
                        has_next=False,
                        has_previous=False
                    ).model_dump()
                }
            
            # Calculate pagination
            start = (page - 1) * limit
            end = start + limit - 1
            
            # Get notification IDs
            notification_ids = await redis_manager.client.lrange(user_key, start, end)
            
            # Get full notification data
            notifications = []
            for notif_id in notification_ids:
                notif_data = await self._get_status_from_cache(notif_id)
                if notif_data:
                    notifications.append(notif_data)
            
            # Calculate meta
            total_pages = (total + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1
            
            return {
                "success": True,
                "data": notifications,
                "message": f"Retrieved {len(notifications)} notifications",
                "error": None,
                "meta": PaginationMeta(
                    total=total,
                    limit=limit,
                    page=page,
                    total_pages=total_pages,
                    has_next=has_next,
                    has_previous=has_previous
                ).model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "message": "Failed to retrieve notifications",
                "meta": None
            }
