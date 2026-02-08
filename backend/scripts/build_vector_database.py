"""
Production script to build the complete vector database.
Processes all documents and creates the searchable index.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexers import DocumentProcessor
from src.rag import VectorStore
from src.utils import log


def build_vector_database(
    confluence_dir: str = None,
    github_dir: str = None,
    vector_db_dir: str = "./chroma_db",
    collection_name: str = "ai_sme_documents"
) -> int:
    """
    Build the complete vector database.
    
    Args:
        confluence_dir: Path to Confluence JSON directory (relative or absolute)
        github_dir: Path to GitHub JSON directory (relative or absolute)
        vector_db_dir: Directory for ChromaDB (default: ./chroma_db)
        collection_name: Collection name (default: ai_sme_documents)
    
    Returns:
        0 on success, 1 on failure
    """
    # Use relative paths if not provided (works both locally and in Railway)
    if confluence_dir is None:
        # Try relative path first (works if data/ is in backend/ or project root)
        base_path = Path(__file__).parent.parent.parent
        confluence_dir = str(base_path / "data" / "raw" / "confluence")
        # Fallback: try backend/data if data/ is in backend/
        if not Path(confluence_dir).exists():
            confluence_dir = str(Path(__file__).parent.parent / "data" / "raw" / "confluence")
    
    if github_dir is None:
        base_path = Path(__file__).parent.parent.parent
        github_dir = str(base_path / "data" / "raw" / "github")
        if not Path(github_dir).exists():
            github_dir = str(Path(__file__).parent.parent / "data" / "raw" / "github")
    
    log.info(f"\n🔨 Building vector database...")
    log.info(f"Confluence dir: {confluence_dir}")
    log.info(f"GitHub dir: {github_dir}")
    log.info(f"Vector DB dir: {vector_db_dir}")
    
    try:
        processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
        vector_store = VectorStore(persist_directory=vector_db_dir, collection_name=collection_name)
        
        # Check if data directories exist
        confluence_exists = Path(confluence_dir).exists()
        github_exists = Path(github_dir).exists()
        
        if not confluence_exists and not github_exists:
            log.error("❌ Data directories not found!")
            log.error(f"   Confluence: {confluence_dir} (exists: {confluence_exists})")
            log.error(f"   GitHub: {github_dir} (exists: {github_exists})")
            return 1
        
        log.info("Processing documents and generating embeddings...")
        processed_chunks = processor.process_from_directories(
            confluence_dir=confluence_dir if confluence_exists else None,
            github_dir=github_dir if github_exists else None,
            generate_embeddings=True
        )
        
        all_chunks = []
        for source_type, chunks in processed_chunks.items():
            all_chunks.extend(chunks)
        
        if not all_chunks:
            log.error("❌ No chunks processed! Check data directories.")
            return 1
        
        log.info(f"Indexing {len(all_chunks)} chunks into vector database...")
        added_count = vector_store.add_documents(all_chunks)
        
        stats = vector_store.get_stats()
        
        log.info(f"\n✅ Vector database built successfully")
        log.info(f"   Total documents: {stats['total_documents']}")
        log.info(f"   Location: {stats['persist_directory']}")
        
        return 0
        
    except Exception as e:
        log.error(f"Build failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        return 1


def main():
    """CLI entry point."""
    sys.exit(build_vector_database())


if __name__ == "__main__":
    sys.exit(main())
