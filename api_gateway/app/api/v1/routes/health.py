# app/api/v1/routes/health.py
from fastapi import APIRouter, status
from datetime import datetime

from app.core.redis import redis_manager
from app.core.rabbitmq import rabbitmq_manager
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "api-gateway",
        "version": settings.VERSION
    }
    
    # Check Redis
    try:
        await redis_manager.client.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"disconnected: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check RabbitMQ
    try:
        if rabbitmq_manager.connection and not rabbitmq_manager.connection.is_closed:
            health_status["rabbitmq"] = "connected"
        else:
            health_status["rabbitmq"] = "disconnected"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["rabbitmq"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return health_status


@router.get("/metrics")
async def get_metrics():
    """
    Metrics endpoint for monitoring (Prometheus format optional)
    """
    # In production, integrate with Prometheus client
    return {
        "total_notifications_sent": 0,  # Would come from Redis counter
        "queue_lengths": {
            "email": 0,
            "push": 0,
            "failed": 0
        },
        "success_rate": 0.0,
        "average_response_time_ms": 0.0
    }
