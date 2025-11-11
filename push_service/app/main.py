from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
from app.config import settings
from app.api.routes import router
from app.services.rabbitmq_consumer import rabbitmq_consumer
from app.utils.logger import logger


# Consumer thread
consumer_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Start RabbitMQ consumer in separate thread
    global consumer_thread
    consumer_thread = threading.Thread(
        target=rabbitmq_consumer.start_consuming,
        daemon=True
    )
    consumer_thread.start()
    logger.info("RabbitMQ consumer thread started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Push Service...")
    rabbitmq_consumer.stop_consuming()
    if consumer_thread:
        consumer_thread.join(timeout=5)
    logger.info("Push Service shut down complete")


# Create FastAPI app
app = FastAPI(
    title="Push Notification Service",
    description="Microservice for sending push notifications via Firebase FCM",
    version=settings.service_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )