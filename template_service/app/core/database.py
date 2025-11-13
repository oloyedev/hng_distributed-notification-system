
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Index
from datetime import datetime
from typing import Optional, AsyncGenerator

from app.core.config import get_settings
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)

# Database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Template(Base):
    """Template model"""
    __tablename__ = "templates_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default="en", index=True)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    __table_args__ = (
        Index('idx_template_code_language_version', 'template_code', 'language', 'version'),
        Index('idx_template_code_active', 'template_code', 'is_active'),
    )


async def init_db():
    """Initialize database - create tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session
    Generator function for dependency injection
    """
    async with AsyncSessionLocal() as session:
        yield session