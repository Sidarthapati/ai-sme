"""
Health check and status endpoints.
"""

from fastapi import APIRouter
from ..api.models import HealthResponse
from ..config import settings
from ..rag import VectorStore

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "vector_db": {
            "type": settings.vector_db_type,
            "status": "connected"
        }
    }


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health():
    """Detailed health check with vector DB stats."""
    try:
        vector_store = VectorStore()
        stats = vector_store.get_stats()
        
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "vector_db": {
                "type": settings.vector_db_type,
                "status": "connected",
                "documents": stats.get("total_documents", 0),
                "collection": stats.get("collection_name", ""),
                "source_breakdown": stats.get("source_breakdown", {})
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "app": settings.app_name,
            "version": settings.app_version,
            "vector_db": {
                "type": settings.vector_db_type,
                "status": "error",
                "error": str(e)
            }
        }
