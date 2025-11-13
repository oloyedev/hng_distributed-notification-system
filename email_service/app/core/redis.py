
import redis.asyncio as redis
from typing import Optional
import json
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager with functional interface"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            if settings.REDIS_URL:
                self.client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
            else:
                self.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    encoding="utf-8",
                    decode_responses=True
                )
            
            # Test connection
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis - Pure interface"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis - Side effect isolated"""
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """
        Get JSON value from Redis
        Pure function composition: get -> parse
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON for key {key}")
                return None
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: dict, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set JSON value in Redis
        Pure function composition: serialize -> set
        """
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            logger.error(f"Failed to set JSON for key {key}: {e}")
            return False



_redis_manager = RedisManager()


async def connect_redis():
    """Connect to Redis - Module level function"""
    await _redis_manager.connect()


async def close_redis():
    """Close Redis connection - Module level function"""
    await _redis_manager.close()


def get_redis_client() -> RedisManager:
    """
    Get Redis client instance
    Pure function - returns same instance
    """
    return _redis_manager