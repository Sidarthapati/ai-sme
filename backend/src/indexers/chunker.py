"""
Document chunking utilities.
Splits documents into optimal chunks for embedding and retrieval.
"""

from typing import List, Dict
import tiktoken

from ..utils import log


class DocumentChunker:
    """
    Chunks documents into smaller pieces for optimal embedding and retrieval.
    Uses token-based chunking to respect model limits.
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
            encoding_name: Tokenizer encoding (cl100k_base for OpenAI)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        log.info(f"Initialized chunker: size={chunk_size}, overlap={chunk_overlap}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into smaller pieces with overlap.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            return []
        
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        
        # If text is smaller than chunk size, return as single chunk
        if total_tokens <= self.chunk_size:
            return [{
                'content': text,
                'token_count': total_tokens,
                'chunk_index': 0,
                'total_chunks': 1,
                **(metadata or {})
            }]
        
        # Create overlapping chunks
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < total_tokens:
            # Get chunk tokens
            end = min(start + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            
            chunks.append({
                'content': chunk_text,
                'token_count': len(chunk_tokens),
                'chunk_index': chunk_index,
                'total_chunks': 0,  # Will update after loop
                'start_token': start,
                'end_token': end,
                **(metadata or {})
            })
            
            # Move to next chunk with overlap
            start += self.chunk_size - self.chunk_overlap
            chunk_index += 1
        
        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk['total_chunks'] = total_chunks
        
        log.debug(f"Chunked {total_tokens} tokens into {total_chunks} chunks")
        return chunks
    
    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        Chunk a document with its metadata.
        
        Args:
            document: Document dictionary with 'content' and other fields
            
        Returns:
            List of chunk dictionaries
        """
        content = document.get('content', '')
        
        # Extract metadata (everything except content)
        metadata = {k: v for k, v in document.items() if k != 'content'}
        
        # Chunk the content
        chunks = self.chunk_text(content, metadata)
        
        # Add unique chunk IDs
        base_id = document.get('id', 'unknown')
        for i, chunk in enumerate(chunks):
            chunk['chunk_id'] = f"{base_id}_chunk_{i}"
        
        return chunks
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        log.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks


# Convenience function
def chunk_documents(
    documents: List[Dict],
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> List[Dict]:
    """
    Quick function to chunk documents.
    
    Args:
        documents: List of document dictionaries
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Overlapping tokens between chunks
        
    Returns:
        List of chunks
    """
    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_documents(documents)
