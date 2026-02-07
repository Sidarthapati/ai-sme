"""
Main application entry point for AI SME FastAPI backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.config import settings
from src.utils import log
from src.api import chat_router, documents_router, health_router
from src.api.auth import router as auth_router
from src.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Initializes database and vector store.
    """
    log.info("🚀 Starting AI SME application...")
    log.info(f"Environment: {'DEBUG' if settings.debug else 'PRODUCTION'}")
    log.info(f"Vector DB: {settings.vector_db_type}")
    log.info(f"LLM Model: {settings.openai_model}")
    
    # Initialize database
    try:
        await init_db()
        log.info("✅ Database initialized")
    except Exception as e:
        log.error(f"❌ Database initialization failed: {e}")
        # Don't fail startup if DB is not available (for development)
        if not settings.debug:
            raise
    
    # TODO: Initialize vector store
    # TODO: Load any cached models
    
    yield
    
    # Cleanup
    log.info("👋 Shutting down AI SME application...")
    # TODO: Close connections, cleanup resources


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered assistant for documentation and code queries",
    lifespan=lifespan,
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "message": "AI SME API is operational"
    }


# Include API routers
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")


if __name__ == "__main__":
    log.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
