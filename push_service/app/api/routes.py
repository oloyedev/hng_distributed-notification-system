from fastapi import APIRouter, HTTPException
from app.models.schemas import HealthResponse, ApiResponse
from app.config import settings
from app.services.rabbitmq_consumer import rabbitmq_consumer
from app.services.fcm_service import fcm_service
from app.services.circuit_breaker import fcm_circuit_breaker
from app.utils.idempotency import idempotency_manager
from datetime import datetime

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring
    """
    rabbitmq_healthy = rabbitmq_consumer.health_check()
    fcm_healthy = fcm_service.health_check()
    redis_healthy = idempotency_manager.health_check()
    circuit_breaker_state = fcm_circuit_breaker.get_state()
    
    overall_status = "healthy" if all([
        rabbitmq_healthy,
        fcm_healthy,
        redis_healthy
    ]) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.service_version,
        timestamp=datetime.utcnow(),
        checks={
            "rabbitmq": "connected" if rabbitmq_healthy else "disconnected",
            "firebase_fcm": "initialized" if fcm_healthy else "not_initialized",
            "redis": "connected" if redis_healthy else "disconnected",
            "circuit_breaker": circuit_breaker_state
        }
    )


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus-style metrics endpoint
    """
    circuit_state = fcm_circuit_breaker.get_state()
    
    metrics = {
        "push_service_up": 1,
        "rabbitmq_connected": 1 if rabbitmq_consumer.health_check() else 0,
        "fcm_initialized": 1 if fcm_service.health_check() else 0,
        "redis_connected": 1 if idempotency_manager.health_check() else 0,
        "circuit_breaker_state": circuit_state["state"],
        "circuit_breaker_failures": circuit_state["failure_count"]
    }
    
    return ApiResponse(
        success=True,
        data=metrics,
        message="Metrics retrieved successfully",
        meta=None
    )


@router.get("/")
async def root():
    """
    Root endpoint
    """
    return ApiResponse(
        success=True,
        data={
            "service": settings.service_name,
            "version": settings.service_version,
            "status": "running"
        },
        message="Push Service is running",
        meta=None
    )