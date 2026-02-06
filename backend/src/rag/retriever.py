"""
Document retriever for RAG pipeline.
Handles semantic search and document retrieval from vector store.
"""

from typing import List, Dict, Optional
from .vector_store import VectorStore
from ..indexers.embeddings import EmbeddingService
from ..config import settings
from ..utils import log


class Retriever:
    """
    Retrieves relevant documents from vector store based on queries.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ):
        """
        Initialize the retriever.
        
        Args:
            vector_store: VectorStore instance (creates new if None)
            top_k: Number of documents to retrieve
            min_score: Minimum similarity score threshold
        """
        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k
        self.min_score = min_score
        self.embedding_service = EmbeddingService()
        
        log.info(f"Initialized retriever: top_k={top_k}, min_score={min_score}")
    
    def retrieve(
        self,
        query: str,
        source_type: Optional[str] = None,
        n_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User's question
            source_type: Optional filter by source type ('confluence' or 'github')
            n_results: Number of results (uses top_k if None)
        
        Returns:
            List of relevant documents with metadata
        """
        n_results = n_results or self.top_k
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        if not query_embedding:
            log.warning("Failed to generate query embedding")
            return []
        
        # Build where clause for filtering
        where_clause = None
        if source_type:
            where_clause = {"source_type": source_type}
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        documents = []
        for i, (doc_id, doc_content, metadata, distance) in enumerate(zip(
            results['ids'],
            results['documents'],
            results['metadatas'],
            results['distances']
        )):
            # Convert distance to similarity score (lower distance = higher similarity)
            similarity_score = 1.0 - distance if distance <= 1.0 else 0.0
            
            # Filter by minimum score
            if similarity_score < self.min_score:
                continue
            
            documents.append({
                'id': doc_id,
                'content': doc_content,
                'title': metadata.get('title', 'Untitled'),
                'url': metadata.get('url', ''),
                'source_type': metadata.get('source_type', 'unknown'),
                'file_path': metadata.get('file_path', ''),
                'repo_name': metadata.get('repo_name', ''),
                'language': metadata.get('language', ''),
                'start_line': metadata.get('start_line'),
                'end_line': metadata.get('end_line'),
                'similarity_score': similarity_score,
                'distance': distance
            })
        
        log.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
        return documents
    
    def retrieve_hybrid(
        self,
        query: str,
        source_type: Optional[str] = None,
        n_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Hybrid retrieval: semantic search + keyword matching.
        Currently just semantic, but can be extended.
        
        Args:
            query: User's question
            source_type: Optional filter by source type
            n_results: Number of results
        
        Returns:
            List of relevant documents
        """
        # For now, just use semantic search
        # Can add keyword search and re-ranking later
        return self.retrieve(query, source_type, n_results)
    
    def format_sources(self, documents: List[Dict]) -> List[Dict]:
        """
        Format retrieved documents for display.
        
        Args:
            documents: List of retrieved documents
        
        Returns:
            Formatted documents with display-friendly fields
        """
        formatted = []
        
        for doc in documents:
            formatted.append({
                'title': doc.get('title', 'Untitled'),
                'url': doc.get('url', ''),
                'source_type': doc.get('source_type', 'unknown'),
                'content_preview': doc.get('content', '')[:200] + '...' if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                'similarity_score': round(doc.get('similarity_score', 0), 3),
                'metadata': {
                    'file_path': doc.get('file_path'),
                    'repo_name': doc.get('repo_name'),
                    'language': doc.get('language'),
                    'start_line': doc.get('start_line'),
                    'end_line': doc.get('end_line')
                }
            })
        
        return formatted
