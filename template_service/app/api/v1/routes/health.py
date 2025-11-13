# template_service/app/api/v1/routes/health.py
"""
Health check endpoints for Template Service - Pure functional approach
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict
from sqlalchemy import text

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.core.database import AsyncSessionLocal

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check endpoint
    Returns service health status with dependencies
    """
    health_data = create_base_health_data()
    
    # Check Redis
    redis_status = await check_redis_health()
    health_data["redis"] = redis_status
    
    # Check Database
    db_status = await check_database_health()
    health_data["database"] = db_status
    
    # Update overall status
    health_data["status"] = calculate_overall_status(health_data)
    
    return health_data


@router.get("/health/ready")
async def readiness_check() -> Dict:
    """
    Readiness check - is service ready to accept requests
    """
    redis_client = get_redis_client()
    
    try:
        # Check Redis
        await redis_client.client.ping()
        
        # Check Database
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/live")
async def liveness_check() -> Dict:
    """
    Liveness check - is service alive
    """
    return {
        "alive": True,
        "service": settings.APP_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def get_metrics() -> Dict:
    """
    Basic metrics endpoint
    In production, integrate with Prometheus
    """
    return {
        "total_templates": await get_template_count(),
        "cache_hit_rate": 0.0,  # Would calculate from Redis stats
        "active_connections": 0
    }


# Pure helper functions

def create_base_health_data() -> Dict:
    """
    Create base health data structure
    Pure function
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }


async def check_redis_health() -> str:
    """
    Check Redis connection health
    Side effect isolated
    """
    try:
        redis_client = get_redis_client()
        await redis_client.client.ping()
        return "connected"
    except Exception as e:
        return f"disconnected: {str(e)}"


async def check_database_health() -> str:
    """
    Check database connection health
    Side effect isolated
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return "connected"
    except Exception as e:
        return f"disconnected: {str(e)}"


def calculate_overall_status(health_data: Dict) -> str:
    """
    Calculate overall health status
    Pure function - based on dependency statuses
    """
    redis_healthy = "connected" in health_data.get("redis", "")
    db_healthy = "connected" in health_data.get("database", "")
    
    if redis_healthy and db_healthy:
        return "healthy"
    elif db_healthy:
        return "degraded"  # Can work without Redis
    else:
        return "unhealthy"


async def get_template_count() -> int:
    """Get total template count"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM templates WHERE is_active = true")
            )
            return result.scalar() or 0
    except Exception:
        return 0


def create_error_response(error: str) -> Dict:
    """
    Create error response
    Pure function
    """
    return {
        "status": "error",
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }