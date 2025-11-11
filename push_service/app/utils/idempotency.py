import redis
from app.config import settings
from app.utils.logger import logger


class IdempotencyManager:
    """
    Manages idempotency using Redis to prevent duplicate notifications
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        self.ttl = settings.idempotency_ttl
    
    def is_processed(self, request_id: str) -> bool:
        """
        Check if a request has already been processed
        """
        try:
            key = f"idempotency:push:{request_id}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking idempotency: {e}", extra={"correlation_id": request_id})
            return False
    
    def mark_processed(self, request_id: str, result: str) -> bool:
        """
        Mark a request as processed with TTL
        """
        try:
            key = f"idempotency:push:{request_id}"
            self.redis_client.setex(key, self.ttl, result)
            return True
        except Exception as e:
            logger.error(f"Error marking request as processed: {e}", extra={"correlation_id": request_id})
            return False
    
    def get_result(self, request_id: str) -> str | None:
        """
        Get the cached result of a processed request
        """
        try:
            key = f"idempotency:push:{request_id}"
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Error getting cached result: {e}", extra={"correlation_id": request_id})
            return None
    
    def health_check(self) -> bool:
        """
        Check Redis connection health
        """
        try:
            return self.redis_client.ping()
        except Exception:
            return False


idempotency_manager = IdempotencyManager()