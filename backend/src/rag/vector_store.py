"""
Vector store interface using ChromaDB.
Stores and retrieves document embeddings for semantic search.
"""

from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from pathlib import Path
import uuid

from ..config import settings
from ..utils import log


class VectorStore:
    """
    Vector database interface using ChromaDB.
    Handles storage and retrieval of document embeddings.
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "ai_sme_documents"
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        
        # Create persist directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "AI SME document embeddings"}
        )
        
        log.info(f"Initialized vector store: {self.persist_directory}")
        log.info(f"Collection: {collection_name} ({self.collection.count()} documents)")
    
    def add_documents(
        self,
        documents: List[Dict],
        batch_size: int = 100
    ) -> int:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries with 'embedding' field
            batch_size: Number of documents to add per batch
            
        Returns:
            Number of documents added
        """
        if not documents:
            log.warning("No documents to add")
            return 0
        
        log.info(f"Adding {len(documents)} documents to vector store")
        
        added_count = 0
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Prepare batch data
            ids = []
            embeddings = []
            metadatas = []
            documents_text = []
            
            for doc in batch:
                # Generate ID if not present
                doc_id = doc.get('chunk_id') or doc.get('id') or str(uuid.uuid4())
                
                # Get embedding
                embedding = doc.get('embedding')
                if not embedding:
                    log.warning(f"Document {doc_id} has no embedding, skipping")
                    continue
                
                # Prepare metadata (everything except content and embedding)
                metadata = {
                    k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in doc.items()
                    if k not in ['content', 'embedding'] and v is not None
                }
                
                # Add to batch
                ids.append(doc_id)
                embeddings.append(embedding)
                metadatas.append(metadata)
                documents_text.append(doc.get('content', ''))
            
            # Add batch to collection
            if ids:
                try:
                    self.collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        documents=documents_text
                    )
                    added_count += len(ids)
                    log.info(f"Added batch {i // batch_size + 1}: {len(ids)} documents")
                except Exception as e:
                    log.error(f"Error adding batch: {e}")
        
        log.info(f"Successfully added {added_count} documents to vector store")
        return added_count
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar documents using embedding.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filters
            
        Returns:
            Dictionary with ids, documents, metadatas, and distances
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            # Flatten results (query returns list of lists)
            return {
                'ids': results['ids'][0] if results['ids'] else [],
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else []
            }
        except Exception as e:
            log.error(f"Error searching vector store: {e}")
            return {'ids': [], 'documents': [], 'metadatas': [], 'distances': []}
    
    def search_by_text(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Search using text query (requires embedding service).
        
        Args:
            query_text: Text query
            n_results: Number of results to return
            where: Optional metadata filters
            
        Returns:
            Search results
        """
        from ..indexers.embeddings import EmbeddingService
        
        # Generate embedding for query
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.embed_text(query_text)
        
        return self.search(query_embedding, n_results, where)
    
    def get_by_id(self, doc_id: str) -> Optional[Dict]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dictionary or None
        """
        try:
            result = self.collection.get(ids=[doc_id])
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception as e:
            log.error(f"Error getting document {doc_id}: {e}")
            return None
    
    def delete_by_id(self, doc_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[doc_id])
            log.info(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            log.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def count(self) -> int:
        """Get total number of documents in collection."""
        return self.collection.count()
    
    def reset(self):
        """Delete all documents from the collection."""
        log.warning("Resetting vector store - deleting all documents")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "AI SME document embeddings"}
        )
        log.info("Vector store reset complete")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        total_docs = self.count()
        
        # Get sample to analyze
        sample = self.collection.peek(limit=100)
        
        # Count by source type
        source_counts = {}
        if sample['metadatas']:
            for metadata in sample['metadatas']:
                source = metadata.get('source_type', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'total_documents': total_docs,
            'collection_name': self.collection_name,
            'persist_directory': self.persist_directory,
            'source_breakdown': source_counts
        }


# Convenience function
def create_vector_store(
    persist_directory: Optional[str] = None,
    collection_name: str = "ai_sme_documents"
) -> VectorStore:
    """
    Quick function to create a vector store.
    
    Args:
        persist_directory: Directory to persist the database
        collection_name: Name of the collection
        
    Returns:
        VectorStore instance
    """
    return VectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name
    )
