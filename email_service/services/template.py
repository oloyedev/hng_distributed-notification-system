
import httpx
from typing import Dict, Optional
from functools import lru_cache

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


async def fetch_and_render_template(
    template_code: str,
    variables: Dict,
    language: str = "en"
) -> Dict:

    try:
        # Try cache first
        cached_template = await get_cached_template(template_code, language)
        
        if cached_template:
            logger.info(f"Template found in cache: {template_code}")
            return create_template_result(
                success=True,
                data=cached_template
            )
        
        # Fetch from Template Service
        template_result = await fetch_template_from_service(
            template_code,
            variables,
            language
        )
        
        if not template_result["success"]:
            return template_result
        
        # Cache for future use
        await cache_template(
            template_code,
            language,
            template_result["data"]
        )
        
        return template_result
        
    except Exception as e:
        logger.error(f"Error fetching template: {e}")
        return create_template_result(
            success=False,
            error=str(e)
        )


async def fetch_template_from_service(
    template_code: str,
    variables: Dict,
    language: str
) -> Dict:
    """
    Fetch and render template from Template Service
    Pure function with side effects isolated
    """
    try:
        url = f"{settings.TEMPLATE_SERVICE_URL}/api/v1/templates/render"
        
        payload = {
            "template_code": template_code,
            "variables": variables,
            "language": language
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    return create_template_result(
                        success=True,
                        data=data.get("data")
                    )
                else:
                    return create_template_result(
                        success=False,
                        error=data.get("error", "Unknown error from template service")
                    )
            else:
                return create_template_result(
                    success=False,
                    error=f"Template service returned {response.status_code}"
                )
                
    except httpx.TimeoutException:
        logger.error("Template service timeout")
        return create_template_result(
            success=False,
            error="Template service timeout"
        )
    except Exception as e:
        logger.error(f"Error calling template service: {e}")
        return create_template_result(
            success=False,
            error=str(e)
        )


async def get_cached_template(template_code: str, language: str) -> Optional[Dict]:
    """
    Get template from Redis cache
    """
    try:
        redis = get_redis_client()
        cache_key = create_cache_key(template_code, language)
        
        cached_data = await redis.get_json(cache_key)
        return cached_data
        
    except Exception as e:
        logger.error(f"Error getting cached template: {e}")
        return None


async def cache_template(template_code: str, language: str, template_data: Dict) -> bool:
    """
    Cache template in Redis
    """
    try:
        redis = get_redis_client()
        cache_key = create_cache_key(template_code, language)
        
        # Cache for 1 hour
        await redis.set_json(cache_key, template_data, ttl=3600)
        return True
        
    except Exception as e:
        logger.error(f"Error caching template: {e}")
        return False


def create_cache_key(template_code: str, language: str) -> str:
    """
    Create cache key for template
    Pure function
    """
    return f"template:{template_code}:{language}"


def create_template_result(success: bool, data: any = None, error: str = None) -> Dict:
    """
    Create standardized template result
    Pure function
    """
    return {
        "success": success,
        "data": data,
        "error": error
    }