# app/middleware/rate_limit.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import time

from app.core.redis import redis_manager
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    
    Limits requests per user/IP per minute
    """
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/api/v1/health", "/api/v1/metrics"]:
            return await call_next(request)
        
        # Get identifier (user ID from auth or IP address)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        is_allowed, retry_after = await self._check_rate_limit(identifier)
        
        if not is_allowed:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {retry_after} seconds",
                    "data": None,
                    "meta": None
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        response = await call_next(request)
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user ID from auth header
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            return f"apikey:{api_key[:10]}"  # Use first 10 chars of API key
        
        if auth_header:
            return f"token:{auth_header[:20]}"  # Use part of token
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, identifier: str) -> tuple[bool, int]:
        """
        Check if request is within rate limit
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        try:
            key = f"ratelimit:{identifier}"
            
            # Get current count
            current_count = await redis_manager.client.get(key)
            
            if current_count is None:
                # First request, set count to 1 with 60 second expiry
                await redis_manager.client.setex(key, 60, 1)
                return True, 0
            
            current_count = int(current_count)
            
            if current_count >= settings.RATE_LIMIT_PER_MINUTE:
                # Rate limit exceeded
                ttl = await redis_manager.client.ttl(key)
                retry_after = max(ttl, 1)
                logger.warning(f"Rate limit exceeded for {identifier}")
                return False, retry_after
            
            # Increment count
            await redis_manager.client.incr(key)
            return True, 0
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow request (fail open)
            return True, 0
