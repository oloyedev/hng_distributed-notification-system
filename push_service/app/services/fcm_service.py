import firebase_admin
from firebase_admin import credentials, messaging
from typing import Dict, Any
from app.config import settings
from app.models.schemas import PushMessage
from app.utils.logger import logger
from app.services.circuit_breaker import fcm_circuit_breaker, CircuitBreakerOpenError
from app.services.retry_handler import RetryableError, NonRetryableError
import os


class FCMService:
    """
    Firebase Cloud Messaging service for sending push notifications
    """
    
    def __init__(self):
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """
        Initialize Firebase Admin SDK
        """
        try:
            if not firebase_admin._apps:
                cred_path = settings.firebase_credentials_path
                
                if not os.path.exists(cred_path):
                    logger.error(f"Firebase credentials file not found: {cred_path}")
                    return
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                self.initialized = True
                logger.info("Firebase Admin SDK already initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.initialized = False
    
    def send_push(
        self,
        device_token: str,
        push_message: PushMessage,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Send push notification via FCM with circuit breaker protection
        """
        if not self.initialized:
            raise NonRetryableError("Firebase not initialized")
        
        try:
            # Use circuit breaker to protect against FCM failures
            result = fcm_circuit_breaker.call(
                self._send_fcm_message,
                device_token,
                push_message,
                request_id
            )
            return result
        except CircuitBreakerOpenError as e:
            logger.error(
                f"Circuit breaker open, skipping FCM call",
                extra={"correlation_id": request_id}
            )
            raise RetryableError(str(e))
        except Exception as e:
            logger.error(
                f"FCM send failed: {e}",
                extra={"correlation_id": request_id}
            )
            raise
    
    def _send_fcm_message(
        self,
        device_token: str,
        push_message: PushMessage,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Internal method to send FCM message
        """
        try:
            # Validate device token
            if not device_token or len(device_token) < 10:
                raise NonRetryableError("Invalid device token")
            
            # Build FCM message
            notification = messaging.Notification(
                title=push_message.title,
                body=push_message.body,
                image=push_message.image_url
            )
            
            # Build data payload
            data = push_message.data or {}
            data["request_id"] = request_id
            
            # Add click action if provided
            android_config = None
            apns_config = None
            
            if push_message.click_action:
                android_config = messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        click_action=push_message.click_action
                    )
                )
                apns_config = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            category=push_message.click_action
                        )
                    )
                )
            
            # Create FCM message
            message = messaging.Message(
                notification=notification,
                data=data,
                token=device_token,
                android=android_config,
                apns=apns_config
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(
                f"Push notification sent successfully: {response}",
                extra={"correlation_id": request_id}
            )
            
            return {
                "success": True,
                "message_id": response,
                "request_id": request_id
            }
            
        except messaging.UnregisteredError:
            # Device token is invalid/unregistered - don't retry
            logger.warning(
                f"Device token unregistered",
                extra={"correlation_id": request_id}
            )
            raise NonRetryableError("Device token unregistered")
        
        except messaging.InvalidArgumentError as e:
            # Invalid message format - don't retry
            logger.error(
                f"Invalid FCM message: {e}",
                extra={"correlation_id": request_id}
            )
            raise NonRetryableError(f"Invalid message: {e}")
        
        except (messaging.InternalError, messaging.UnavailableError) as e:
            # Temporary FCM service issues - retry
            logger.warning(
                f"FCM temporary error: {e}",
                extra={"correlation_id": request_id}
            )
            raise RetryableError(f"FCM service error: {e}")
        
        except Exception as e:
            # Unknown error - retry with caution
            logger.error(
                f"Unexpected FCM error: {e}",
                extra={"correlation_id": request_id}
            )
            raise RetryableError(f"Unexpected error: {e}")
    
    def health_check(self) -> bool:
        """
        Check if FCM service is healthy
        """
        return self.initialized


fcm_service = FCMService()