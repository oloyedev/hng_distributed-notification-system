# app/core/rabbitmq.py
import aio_pika
from typing import Optional, Dict
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQManager:
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
    
    async def connect(self):
        """Connect to RabbitMQ and setup exchange/queues"""
        try:
            # Create connection
            if settings.RABBITMQ_URL:
                connection_url = settings.RABBITMQ_URL
            else:
                connection_url = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}{settings.RABBITMQ_VHOST}"
            
            self.connection = await aio_pika.connect_robust(connection_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare queues
            await self._declare_queues()
            
            logger.info("RabbitMQ connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def _declare_queues(self):
        """Declare all queues and bind them to exchange"""
        queues_config = [
            (settings.EMAIL_QUEUE, "email"),
            (settings.PUSH_QUEUE, "push"),
            (settings.EMAIL_PRIORITY_QUEUE, "email.priority"),
            (settings.PUSH_PRIORITY_QUEUE, "push.priority"),
            (settings.FAILED_QUEUE, "failed"),
        ]
        
        # Declare dead letter queue first
        dlq = await self.channel.declare_queue(
            settings.FAILED_QUEUE,
            durable=True
        )
        await dlq.bind(self.exchange, routing_key="failed")
        
        # Declare other queues with DLQ
        for queue_name, routing_key in queues_config[:-1]:  # Exclude failed queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": settings.EXCHANGE_NAME,
                    "x-dead-letter-routing-key": "failed"
                }
            )
            await queue.bind(self.exchange, routing_key=routing_key)
            logger.info(f"Queue declared and bound: {queue_name} -> {routing_key}")
    
    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
    
    async def publish_message(
        self,
        routing_key: str,
        message: Dict,
        priority: int = 0,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Publish message to exchange"""
        try:
            message_body = json.dumps(message).encode()
            
            msg = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                priority=priority,
                correlation_id=correlation_id,
                content_type="application/json",
                content_encoding="utf-8"
            )
            
            await self.exchange.publish(
                msg,
                routing_key=routing_key
            )
            
            logger.info(f"Message published to {routing_key}: {message.get('notification_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to {routing_key}: {e}")
            return False
    
    async def publish_to_queue(
        self,
        notification_type: str,
        message: Dict,
        priority: int = 0,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish message to appropriate queue based on type and priority
        
        Args:
            notification_type: 'email' or 'push'
            message: Message payload
            priority: Priority level (0-10, higher is more important)
            correlation_id: Correlation ID for tracking
        """
        # Determine routing key based on type and priority
        if priority >= 5:
            routing_key = f"{notification_type}.priority"
        else:
            routing_key = notification_type
        
        return await self.publish_message(
            routing_key=routing_key,
            message=message,
            priority=priority,
            correlation_id=correlation_id
        )


# Singleton instance
rabbitmq_manager = RabbitMQManager()
