from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import logging

from app.core.config import get_settings
from app.core.rabbitmq import connect_rabbitmq, close_rabbitmq, consume_email_queue
from app.core.redis import connect_redis, close_redis
from app.api.v1.routes import health
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    try:
        await connect_redis()
        connection, channel = await connect_rabbitmq()
        logger.info("All connections established")
        
   
        consumer_task = asyncio.create_task(consume_email_queue(channel))
        
        yield
        
   
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        await close_rabbitmq(connection)
        await close_redis()
        logger.info("All connections closed")
        
    except Exception as e:
        logger.error(f"Failed to establish connections: {e}")
        raise


app = FastAPI(
    title="Email Service",
    description="Processes email notifications from queue",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )