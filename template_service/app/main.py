# template_service/main.py
"""
Template Service - Functional Programming Approach
Manages notification templates with versioning and i18n
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.redis import connect_redis, close_redis
from app.api.v1.routes import template, health
from app.utils.logger import setup_logger
import uvicorn

logger = setup_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    try:
        await init_db()
        await connect_redis()
        logger.info("All connections established")
        
        yield
        
        # Shutdown
        await close_db()
        await close_redis()
        logger.info("All connections closed")
        
    except Exception as e:
        logger.error(f"Failed to establish connections: {e}")
        raise


app = FastAPI(
    title="Template Service",
    description="Manages notification templates with versioning",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(template.router, prefix="/api/v1", tags=["Templates"])


if __name__ == "__main__":
  
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )