import pika
import json
import httpx
from typing import Dict, Any
from app.config import settings
from app.models.schemas import (
    PushNotificationRequest,
    PushMessage,
    NotificationStatus,
    PushNotificationStatus
)
from app.services.fcm_service import fcm_service
from app.services.retry_handler import retry_handler, RetryableError, NonRetryableError
from app.utils.logger import logger
from app.utils.idempotency import idempotency_manager
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, retry_if_result
import time

# Helper function for tenacity to check if we should retry start_consuming
def is_amqp_connection_error(value):
    """Return True if the value is an AMQPConnectionError instance."""
    return isinstance(value, pika.exceptions.AMQPConnectionError)

# Function to run before retrying the consuming loop
def before_retry_log(retry_state):
    logger.warning(
        f"RabbitMQ consumer loop failed (Attempt {retry_state.attempt_number}). Retrying connection and consuming in 3 seconds..."
    )

class RabbitMQConsumer:
    """
    Consumes messages from RabbitMQ push queue and processes push notifications
    """
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.user_service_url = "http://user-service:8001"
        self.gateway_url = settings.api_gateway_url
    
    # RETAIN: Use this for initial connection setup (it succeeds based on your test)
    # The @retry decorator is now removed from here and moved to start_consuming
    def connect(self):
        """
        Establish connection to RabbitMQ (without internal retries)
        """
        credentials = pika.PlainCredentials(
            settings.rabbitmq_user,
            settings.rabbitmq_password
        )
        
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            virtual_host=settings.rabbitmq_vhost,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Add a slight delay to allow the connection to settle
        time.sleep(0.5)
        
        # Declare queues (idempotent)
        self.channel.queue_declare(
            queue=settings.rabbitmq_push_queue,
            durable=True
        )
        self.channel.queue_declare(
            queue=settings.rabbitmq_failed_queue,
            durable=True
        )
        
        # Set QoS (prefetch count)
        self.channel.basic_qos(prefetch_count=settings.message_prefetch_count)
        
        logger.info("Connected to RabbitMQ successfully")
        return True
    
    # --- MODIFIED START_CONSUMING METHOD WITH RETRY LOGIC ---
    @retry(
        # The main consuming loop will automatically attempt to reconnect forever
        stop=stop_after_attempt(99999), 
        wait=wait_fixed(3),           
        # Retry ONLY if the connection dropped (AMQPConnectionError)
        retry=retry_if_exception_type(pika.exceptions.AMQPConnectionError),
        before_sleep=before_retry_log
    )
    def start_consuming(self):
        """
        Start consuming messages from the push queue, with a persistent retry loop
        for connection drops.
        """
        try:
            # 1. Ensure connection is fresh or re-established after a failure
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            logger.info(f"Starting to consume from queue: {settings.rabbitmq_push_queue}")
            
            # 2. Start consuming
            self.channel.basic_consume(
                queue=settings.rabbitmq_push_queue,
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            # 3. Start the blocking loop
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.stop_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            # Propagate AMQPConnectionError to the @retry decorator
            logger.error(f"RabbitMQ connection dropped: {e}")
            self.stop_consuming()
            raise e 
        except Exception as e:
            # Handle non-retryable errors
            logger.error(f"Error in consumer: {e}")
            self.stop_consuming()

    # --- REST OF THE CLASS METHODS (process_message, _get_user_device_token, etc.) REMAIN UNCHANGED ---

    def process_message(self, ch, method, properties, body):
        """
        Process individual push notification message
        """
        request_id = None
        
        try:
            # Parse message
            message_data = json.loads(body.decode())
            notification_request = PushNotificationRequest(**message_data)
            request_id = notification_request.request_id
            
            logger.info(
                f"Processing push notification",
                extra={"correlation_id": request_id}
            )
            
            # Check idempotency
            if idempotency_manager.is_processed(request_id):
                logger.info(
                    f"Request already processed (idempotent)",
                    extra={"correlation_id": request_id}
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Fetch user device token
            device_token = self._get_user_device_token(notification_request.user_id)
            
            if not device_token:
                logger.warning(
                    f"No device token found for user",
                    extra={"correlation_id": request_id}
                )
                self._send_status_update(
                    request_id,
                    NotificationStatus.failed,
                    "No device token found"
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Build push message
            push_message = self._build_push_message(notification_request)
            
            # Send push with retry logic
            try:
                result = retry_handler.with_retry(
                    fcm_service.send_push,
                    device_token,
                    push_message,
                    request_id
                )
                
                # Mark as processed
                idempotency_manager.mark_processed(request_id, "delivered")
                
                # Send success status
                self._send_status_update(
                    request_id,
                    NotificationStatus.delivered,
                    None
                )
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                logger.info(
                    f"Push notification delivered successfully",
                    extra={"correlation_id": request_id}
                )
                
            except NonRetryableError as e:
                # Permanent failure - don't retry
                logger.error(
                    f"Permanent failure: {e}",
                    extra={"correlation_id": request_id}
                )
                
                idempotency_manager.mark_processed(request_id, "failed")
                self._send_status_update(request_id, NotificationStatus.failed, str(e))
                self._send_to_dead_letter_queue(message_data, str(e))
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except RetryableError as e:
                # Retry exhausted - move to DLQ
                logger.error(
                    f"Retries exhausted: {e}",
                    extra={"correlation_id": request_id}
                )
                
                self._send_status_update(request_id, NotificationStatus.failed, str(e))
                self._send_to_dead_letter_queue(message_data, str(e))
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
        except Exception as e:
            logger.error(
                f"Unexpected error processing message: {e}",
                extra={"correlation_id": request_id}
            )
            # Reject and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _get_user_device_token(self, user_id: str) -> str | None:
        """
        Fetch user's device token from User Service
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.user_service_url}/api/v1/users/{user_id}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    return user_data.get("data", {}).get("push_token")
                else:
                    logger.warning(f"Failed to fetch user data: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching user device token: {e}")
            return None
    
    def _build_push_message(self, request: PushNotificationRequest) -> PushMessage:
        """
        Build push message from notification request and template
        """
        # Simple template substitution (you can enhance this)
        title = f"Notification for {request.variables.name}"
        body = f"You have a new notification"
        
        # If template_code contains actual template, use it
        if "{{" in request.template_code:
            body = request.template_code.replace("{{name}}", request.variables.name)
            if request.variables.link:
                body = body.replace("{{link}}", str(request.variables.link))
        
        return PushMessage(
            title=title,
            body=body,
            click_action=str(request.variables.link) if request.variables.link else None,
            data=request.metadata
        )
    
    def _send_status_update(
        self,
        notification_id: str,
        status: NotificationStatus,
        error: str | None
    ):
        """
        Send status update to API Gateway
        """
        try:
            status_update = PushNotificationStatus(
                notification_id=notification_id,
                status=status,
                timestamp=datetime.utcnow(),
                error=error
            )
            
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self.gateway_url}/api/v1/push/status/",
                    json=status_update.model_dump(mode='json')
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to send status update: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
    
    def _send_to_dead_letter_queue(self, message: Dict[str, Any], error: str):
        """
        Send failed message to dead letter queue
        """
        try:
            failed_message = {
                **message,
                "failed_at": datetime.utcnow().isoformat(),
                "error": error,
                "service": "push-service"
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.rabbitmq_failed_queue,
                body=json.dumps(failed_message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"Message sent to dead letter queue")
            
        except Exception as e:
            logger.error(f"Failed to send to dead letter queue: {e}")
    
    def stop_consuming(self):
        """
        Stop consuming and close connections
        """
        try:
            if self.channel:
                # Stop consuming without closing the connection/channel immediately
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                # Give it a moment to process the stop
                self.connection.close() 
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
    
    def health_check(self) -> bool:
        """
        Check RabbitMQ connection health
        """
        try:
            return self.connection and self.connection.is_open
        except Exception:
            return False


rabbitmq_consumer = RabbitMQConsumer()