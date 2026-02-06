"""
Embedding generation service.
Creates vector embeddings for text using OpenAI's embedding models.
"""

from typing import List, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import time

from ..config import settings
from ..utils import log


class EmbeddingService:
    """
    Service for generating embeddings using OpenAI API.
    Includes retry logic and batch processing.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        batch_size: int = 100
    ):
        """
        Initialize the embedding service.
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
            model: Embedding model to use
            batch_size: Number of texts to embed in one API call
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.batch_size = batch_size
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env")
        
        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
        except TypeError as e:
            # Fallback for older OpenAI versions
            import openai as openai_module
            self.client = openai_module.OpenAI(api_key=self.api_key)
        
        log.info(f"Initialized embedding service: model={model}, batch_size={batch_size}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings with retry logic.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            # Extract embeddings in correct order
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            log.error(f"Error creating embeddings: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            log.warning("Empty text provided for embedding")
            return []
        
        embeddings = self._create_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            log.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            try:
                embeddings = self._create_embeddings(batch)
                all_embeddings.extend(embeddings)
                
                # Rate limiting - be nice to API
                if i + self.batch_size < len(texts):
                    time.sleep(0.5)
                    
            except Exception as e:
                log.error(f"Failed to embed batch {batch_num}: {e}")
                # Add empty embeddings for failed batch
                all_embeddings.extend([[] for _ in batch])
        
        log.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def embed_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Add embeddings to documents.
        
        Args:
            documents: List of document dictionaries with 'content' field
            
        Returns:
            Documents with 'embedding' field added
        """
        log.info(f"Embedding {len(documents)} documents")
        
        # Extract texts
        texts = [doc.get('content', '') for doc in documents]
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Add embeddings to documents
        for doc, embedding in zip(documents, embeddings):
            doc['embedding'] = embedding
            doc['embedding_model'] = self.model
        
        return documents


# Convenience function
def embed_documents(
    documents: List[Dict],
    api_key: Optional[str] = None,
    model: str = "text-embedding-3-large"
) -> List[Dict]:
    """
    Quick function to embed documents.
    
    Args:
        documents: List of document dictionaries
        api_key: Optional OpenAI API key
        model: Embedding model to use
        
    Returns:
        Documents with embeddings added
    """
    service = EmbeddingService(api_key=api_key, model=model)
    return service.embed_documents(documents)
