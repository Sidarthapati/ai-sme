"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Chat Models
class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat query request."""
    message: str = Field(..., description="User's question", min_length=1)
    source_type: Optional[str] = Field(None, description="Filter by source: 'confluence' or 'github'")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for multi-turn")
    stream: bool = Field(False, description="Whether to stream the response")


class Source(BaseModel):
    """Source citation."""
    title: str
    url: str
    source_type: str
    similarity_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Chat query response."""
    answer: str
    sources: List[Source]
    context_used: int
    conversation_id: Optional[str] = None


class ChatStreamChunk(BaseModel):
    """Streaming response chunk."""
    type: str = Field(..., description="Chunk type: 'chunk', 'complete', or 'error'")
    content: Optional[str] = None
    answer: Optional[str] = None
    sources: Optional[List[Source]] = None
    context_used: Optional[int] = None


# Document Upload Models
class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    success: bool
    document_id: str
    chunks_created: int
    filename: str
    message: str


class DocumentInfo(BaseModel):
    """Document information."""
    id: str
    title: str
    filename: str
    source_type: str
    uploaded_at: Optional[str] = None
    chunks: int


class DocumentListResponse(BaseModel):
    """List of documents."""
    documents: List[DocumentInfo]
    total: int


class DocumentDeleteResponse(BaseModel):
    """Response after document deletion."""
    success: bool
    message: str


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    app: str
    version: str
    vector_db: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Conversation Models
class ConversationCreate(BaseModel):
    """Create a new conversation."""
    title: Optional[str] = None


class ConversationMessage(BaseModel):
    """Message in a conversation."""
    role: str
    content: str
    timestamp: str


class Conversation(BaseModel):
    """Conversation with messages."""
    id: str
    title: Optional[str]
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str
