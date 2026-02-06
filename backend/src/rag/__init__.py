"""
RAG (Retrieval Augmented Generation) module.

This module contains:
- vector_store.py: Vector database interface (ChromaDB) ✅
- retriever.py: Document retrieval logic ✅
- generator.py: LLM-based response generation ✅
- pipeline.py: Complete RAG pipeline orchestration ✅
- prompts.py: Prompt templates ✅
"""

from .vector_store import VectorStore, create_vector_store
from .retriever import Retriever
from .generator import Generator
from .pipeline import RAGPipeline, create_rag_pipeline
from .prompts import SYSTEM_PROMPT, format_context_for_prompt, build_user_prompt

__all__ = [
    "VectorStore",
    "create_vector_store",
    "Retriever",
    "Generator",
    "RAGPipeline",
    "create_rag_pipeline",
    "SYSTEM_PROMPT",
    "format_context_for_prompt",
    "build_user_prompt",
]
