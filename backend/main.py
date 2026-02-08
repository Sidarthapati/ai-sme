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
from src.rag import VectorStore
from scripts.build_vector_database import build_vector_database


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
    
    # Initialize vector store and auto-rebuild if empty
    try:
        vector_store = VectorStore()
        doc_count = vector_store.collection.count()
        log.info(f"📊 ChromaDB document count: {doc_count}")
        
        # Auto-rebuild if ChromaDB is empty (first deploy or volume was cleared)
        if doc_count == 0:
            log.warning("⚠️  ChromaDB is empty! Auto-rebuilding vector database...")
            log.warning("   This may take a few minutes on first startup...")
            
            result = build_vector_database(
                vector_db_dir=settings.chroma_persist_directory,
                collection_name="ai_sme_documents"
            )
            
            if result == 0:
                # Re-initialize to get updated count
                vector_store = VectorStore()
                final_count = vector_store.collection.count()
                log.info(f"✅ Vector database auto-rebuilt successfully! ({final_count} documents)")
            else:
                log.error("❌ Vector database auto-rebuild failed!")
                log.error("   The app will start, but RAG queries may return no results.")
                log.error("   You can rebuild manually by running: python scripts/build_vector_database.py")
        else:
            log.info(f"✅ Vector store initialized with {doc_count} documents")
            
    except Exception as e:
        log.error(f"❌ Vector store initialization failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        # Don't fail startup - app can run without vector store (for development)
        if not settings.debug:
            log.warning("   Continuing startup without vector store...")
    
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
