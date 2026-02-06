"""
API module containing FastAPI endpoints.

This module contains:
- chat.py: Chat and query endpoints ✅
- documents.py: Document upload and management endpoints ✅
- health.py: Health check and status endpoints ✅
- models.py: Pydantic request/response models ✅
"""

from .chat import router as chat_router
from .documents import router as documents_router
from .health import router as health_router

__all__ = [
    "chat_router",
    "documents_router",
    "health_router",
]
