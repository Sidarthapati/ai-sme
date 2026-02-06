"""
Document processor for loading and preparing documents for indexing.
Reads JSON files from scrapers and prepares them for embedding.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

from ..utils import log
from .chunker import DocumentChunker
from .embeddings import EmbeddingService


class DocumentProcessor:
    """
    Processes documents from raw JSON files through chunking and embedding.
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        embedding_model: str = "text-embedding-3-large"
    ):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlapping tokens between chunks
            embedding_model: OpenAI embedding model to use
        """
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedding_service = EmbeddingService(model=embedding_model)
        
        log.info("Initialized document processor")
    
    def load_json_files(self, directory: Path) -> List[Dict]:
        """
        Load all JSON files from a directory.
        
        Args:
            directory: Path to directory containing JSON files
            
        Returns:
            List of document dictionaries
        """
        directory = Path(directory)
        
        if not directory.exists():
            log.warning(f"Directory does not exist: {directory}")
            return []
        
        documents = []
        json_files = list(directory.glob("*.json"))
        
        log.info(f"Loading {len(json_files)} JSON files from {directory}")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                    documents.append(doc)
            except Exception as e:
                log.error(f"Error loading {json_file}: {e}")
        
        log.info(f"Loaded {len(documents)} documents")
        return documents
    
    def load_all_documents(
        self,
        confluence_dir: Optional[Path] = None,
        github_dir: Optional[Path] = None
    ) -> Dict[str, List[Dict]]:
        """
        Load documents from both Confluence and GitHub directories.
        
        Args:
            confluence_dir: Path to Confluence JSON files
            github_dir: Path to GitHub JSON files
            
        Returns:
            Dictionary with 'confluence' and 'github' document lists
        """
        result = {
            'confluence': [],
            'github': []
        }
        
        if confluence_dir:
            result['confluence'] = self.load_json_files(confluence_dir)
        
        if github_dir:
            result['github'] = self.load_json_files(github_dir)
        
        total = len(result['confluence']) + len(result['github'])
        log.info(f"Loaded {total} total documents ({len(result['confluence'])} Confluence, {len(result['github'])} GitHub)")
        
        return result
    
    def process_documents(
        self,
        documents: List[Dict],
        generate_embeddings: bool = True
    ) -> List[Dict]:
        """
        Process documents: chunk and optionally embed.
        
        Args:
            documents: List of document dictionaries
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            List of processed chunks with embeddings
        """
        log.info(f"Processing {len(documents)} documents")
        
        # Step 1: Chunk documents
        log.info("Step 1: Chunking documents...")
        chunks = self.chunker.chunk_documents(documents)
        log.info(f"Created {len(chunks)} chunks")
        
        # Step 2: Generate embeddings (optional)
        if generate_embeddings:
            log.info("Step 2: Generating embeddings...")
            chunks = self.embedding_service.embed_documents(chunks)
            log.info("Embeddings generated")
        
        return chunks
    
    def process_from_directories(
        self,
        confluence_dir: Optional[str] = None,
        github_dir: Optional[str] = None,
        generate_embeddings: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Complete pipeline: load, chunk, and embed documents.
        
        Args:
            confluence_dir: Path to Confluence JSON directory
            github_dir: Path to GitHub JSON directory
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            Dictionary with processed chunks by source type
        """
        # Load documents
        documents = self.load_all_documents(
            confluence_dir=Path(confluence_dir) if confluence_dir else None,
            github_dir=Path(github_dir) if github_dir else None
        )
        
        # Process each source type separately
        result = {}
        
        if documents['confluence']:
            log.info("Processing Confluence documents...")
            result['confluence'] = self.process_documents(
                documents['confluence'],
                generate_embeddings=generate_embeddings
            )
        
        if documents['github']:
            log.info("Processing GitHub documents...")
            result['github'] = self.process_documents(
                documents['github'],
                generate_embeddings=generate_embeddings
            )
        
        total_chunks = sum(len(chunks) for chunks in result.values())
        log.info(f"Processing complete: {total_chunks} total chunks")
        
        return result


# Convenience function
def process_documents_from_files(
    confluence_dir: str,
    github_dir: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    generate_embeddings: bool = True
) -> Dict[str, List[Dict]]:
    """
    Quick function to process documents from directories.
    
    Args:
        confluence_dir: Path to Confluence JSON files
        github_dir: Path to GitHub JSON files
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Overlapping tokens
        generate_embeddings: Whether to generate embeddings
        
    Returns:
        Dictionary with processed chunks
    """
    processor = DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return processor.process_from_directories(
        confluence_dir=confluence_dir,
        github_dir=github_dir,
        generate_embeddings=generate_embeddings
    )
