"""
Indexers module for processing and indexing documents.

This module contains:
- document_processor.py: Process different document types ✅
- chunker.py: Chunk documents for optimal retrieval ✅
- embeddings.py: Generate embeddings for documents ✅
"""

from .document_processor import DocumentProcessor, process_documents_from_files
from .chunker import DocumentChunker, chunk_documents
from .embeddings import EmbeddingService, embed_documents

__all__ = [
    "DocumentProcessor",
    "process_documents_from_files",
    "DocumentChunker",
    "chunk_documents",
    "EmbeddingService",
    "embed_documents",
]
