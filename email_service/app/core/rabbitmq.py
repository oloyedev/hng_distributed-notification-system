# email_service/app/core/rabbitmq.py
import aio_pika
import json
import asyncio
from typing import Tuple, Optional
from functools import partial

from app.core.config import get_settings
from ...services.email import process_email_message
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


async def connect_rabbitmq() -> Tuple[aio_pika.Connection, aio_pika.Channel]:
    """
    Establish connection to RabbitMQ
    Pure function returning connection and channel
    """
    try:
        connection_url = (
            settings.RABBITMQ_URL if settings.RABBITMQ_URL
            else f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
                 f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}{settings.RABBITMQ_VHOST}"
        )
        
        connection = await aio_pika.connect_robust(connection_url)
        channel = await connection.channel()
        
        # Set QoS - prefetch count for fair dispatch
        await channel.set_qos(prefetch_count=settings.PREFETCH_COUNT)
        
        logger.info("RabbitMQ connected successfully")
        return connection, channel
        
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise


async def close_rabbitmq(connection: aio_pika.Connection) -> None:
    """Close RabbitMQ connection"""
    if connection and not connection.is_closed:
        await connection.close()
        logger.info("RabbitMQ connection closed")


async def consume_email_queue(channel: aio_pika.Channel) -> None:
    """
    Consume messages from email queues
    Functional approach using async iteration
    """
    try:
        # Get queues
        email_queue = await channel.get_queue(settings.EMAIL_QUEUE)
        priority_queue = await channel.get_queue(settings.EMAIL_PRIORITY_QUEUE)
        
        logger.info(f"Starting to consume from {settings.EMAIL_QUEUE} and {settings.EMAIL_PRIORITY_QUEUE}")
        
        # Create async tasks for both queues
        tasks = [
            consume_queue(email_queue, "email"),
            consume_queue(priority_queue, "priority_email")
        ]
        
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Error in consume_email_queue: {e}")
        raise


async def consume_queue(queue: aio_pika.Queue, queue_type: str) -> None:
    """
    Consume messages from a specific queue
    Pure functional approach
    """
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process(requeue=False):
                await handle_message(message, queue_type)


async def handle_message(message: aio_pika.IncomingMessage, queue_type: str) -> None:
    """
    Handle individual message
    Functional composition of processing steps
    """
    try:
        # Parse message
        parsed_message = parse_message(message)
        
        if not parsed_message:
            logger.error("Failed to parse message")
            return
        
        correlation_id = message.correlation_id or parsed_message.get("correlation_id", "unknown")
        notification_id = parsed_message.get("notification_id", "unknown")
        
        logger.info(
            f"Processing {queue_type} message: {notification_id} "
            f"(correlation: {correlation_id})"
        )
        
        # Process email - functional pipeline
        result = await process_email_message(parsed_message)
        
        if result["success"]:
            logger.info(f"Email sent successfully: {notification_id}")
        else:
            logger.error(f"Failed to send email: {notification_id} - {result['error']}")
            
            # Check if we should retry
            if should_retry(parsed_message):
                await retry_message(parsed_message, message.routing_key)
            else:
                await send_to_dlq(parsed_message)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)


def parse_message(message: aio_pika.IncomingMessage) -> Optional[dict]:
    """
    Parse message body to dict
    Pure function
    """
    try:
        body = message.body.decode()
        return json.loads(body)
    except Exception as e:
        logger.error(f"Failed to parse message: {e}")
        return None


def should_retry(message_data: dict) -> bool:
    """
    Determine if message should be retried
    Pure function based on retry count
    """
    retry_count = message_data.get("retry_count", 0)
    max_retries = message_data.get("max_retries", settings.MAX_RETRIES)
    return retry_count < max_retries


async def retry_message(message_data: dict, routing_key: str) -> None:
    """
    Retry failed message with exponential backoff
    """
    try:
        retry_count = message_data.get("retry_count", 0)
        
        # Calculate delay
        delay = calculate_retry_delay(retry_count)
        
        logger.info(
            f"Retrying message {message_data.get('notification_id')} "
            f"in {delay} seconds (attempt {retry_count + 1})"
        )
        
        # Wait before retry
        await asyncio.sleep(delay)
        
        # Increment retry count
        updated_message = {**message_data, "retry_count": retry_count + 1}
        
        # Re-queue message
        await republish_message(updated_message, routing_key)
        
    except Exception as e:
        logger.error(f"Error retrying message: {e}")


def calculate_retry_delay(retry_count: int) -> int:
    """
    Calculate retry delay with exponential backoff
    Pure function
    """
    if settings.EXPONENTIAL_BACKOFF:
        return settings.RETRY_DELAY_SECONDS * (2 ** retry_count)
    return settings.RETRY_DELAY_SECONDS


async def republish_message(message_data: dict, routing_key: str) -> None:
    """
    Republish message to queue for retry
    """
    try:
        # This would require maintaining a connection/channel reference
        # In practice, you'd pass channel as parameter or use dependency injection
        logger.info(f"Re-queuing message: {message_data.get('notification_id')}")
        # Implementation depends on architecture
        
    except Exception as e:
        logger.error(f"Error republishing message: {e}")


async def send_to_dlq(message_data: dict) -> None:
    """
    Send failed message to Dead Letter Queue
    """
    try:
        logger.warning(
            f"Sending message to DLQ: {message_data.get('notification_id')} "
            f"after {message_data.get('retry_count', 0)} retries"
        )
        # Implementation depends on DLQ setup
        
    except Exception as e:
        logger.error(f"Error sending to DLQ: {e}")