"""
Database connection setup using SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from ..config import settings
from ..utils import log
import os

# Create declarative base for models
Base = declarative_base()

# Database URL from environment
# Railway/other platforms provide DATABASE_URL directly
# For local dev, construct from components
if settings.database_url:
    DATABASE_URL = settings.database_url
    # Convert postgresql:// to postgresql+asyncpg:// if needed
    if DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # Construct from components
    db_user = settings.db_user or "postgres"
    db_password = settings.db_password or ""
    db_host = settings.db_host or "localhost"
    db_port = settings.db_port or "5432"
    db_name = settings.db_name or "ai_sme"
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    Use this in FastAPI route dependencies.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    # Import models to register them with Base
    from . import models
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    log.info("Database initialized successfully")
